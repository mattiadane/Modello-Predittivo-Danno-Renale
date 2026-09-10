"""
Modulo Data Access Object (DAO) per la generazione dinamica di query SQL.

Costruisce query complesse con Common Table Expressions (CTE) a cascata
per concatenare cronologicamente parametri clinici all'interno di finestre
di osservazione (OW), di waiting (WW) e di predizione (PW) per eventi AKI.

Inoltre sono scritte altre select per trovare pid della query e rimuovere e interrompere la query ,
e la select per selezionare tutti gli eventi di input dal database
"""

from backend.schema import PipelineInput, ParametroConfig
import re

# Prefisso costante per le viste/tabelle nel DB
C = "v_"

# Mappatura degli alias per le viste temporanee (CTE)
NAME_VIEW = {
    1: "first_param",
    2: "second_param",
    3: "third_param",
    4: "fourth_param",
    5: "fifth_param",
    6: "sixth_param",
}

# Configurazione della struttura e delle chiavi per le tabelle di MIMIC-IV
VIEW_CONFIG = {
    "chartevents": {
        "distinct": "stay_id",
        "label": "",
        "value": "val"
    },
    "inputevents": {
        "distinct": "stay_id",
        "label": "input_name",
        "value": ""
    },
    "labevents": {
        "distinct": "hadm_id",
        "label": "",
        "value": "val"
    },
    "outputevents": {
        "distinct": "stay_id",
        "label": "",
        "value": "val"
    },
    "procedureevents": {
        "distinct": "stay_id",
        "label": "procedure_name",
        "value": ""
    },
    "prescriptions": {
        "distinct": "hadm_id",
        "label": "drug",
        "value": ""
    }
}

# Traduzione delle opzioni di aggregazione da interfaccia a funzioni SQL
AGGREGATION_OPTIONS = {
    "Media": "AVG",
    "Minimo": "MIN",
    "Massimo": "MAX"
}


def sql_alias(name: str) -> str:
    """Escape sicuro delle stringhe per utilizzarle come alias SQL delimitati da doppi apici."""
    cleaned = name.replace('"', '').strip()
    return f"\"{cleaned}\""


def first_tmpv(first_param: ParametroConfig, ow: int) -> dict:
    """
    Genera la prima CTE (first_param) della catena.

    Identifica il punto di partenza temporale (t_0) basato sul primo parametro clinico
    e calcola il limite della finestra di osservazione (end_ow = t_0 + ow hours).

    Args:
        first_param: Configurazioni del primo parametro.
        ow: Durata dell'Observation Window in ore.

    Returns:
        dict: Nome/Alias prodotti e la clausola SQL della prima CTE.
    """
    config = VIEW_CONFIG[first_param.tabella]

    subname = ""
    param_as = []
    select_fields = []
    where_fields = [
        f"itemid = {first_param.id}"
        if first_param.id is not None
        else f"tipo = '{first_param.parametro}'"
    ]
    group_fields = []

    # Gestione delle chiavi esterne e join per tabelle ICU o reparto ospedaliero
    if first_param.tabella not in ("labevents", "prescriptions"):
        select_fields.append("stay_id")
        group_fields.append("stay_id")
        select_fields.append("hadm_id")
        group_fields.append("hadm_id")
    else:
        subname = first_param.tabella[0:2]
        select_fields.append("ic.stay_id")
        group_fields.append("ic.stay_id")
        select_fields.append("ic.hadm_id")
        group_fields.append("ic.hadm_id")
        is_lab = first_param.tabella == "labevents"
        time = "valid_time" if is_lab else "starttime"
        where_fields.append(f"{time} BETWEEN ic.intime and ic.outtime")

    # Gestione dell'aggregazione e del bucket temporale (es. finestre di 6 ore)
    if first_param.aggregazione and first_param.granularita:
        gran_hours = int(first_param.granularita.replace("h", ""))
        gran_seconds = gran_hours * 3600

        group_fields.append(f"FLOOR(EXTRACT(EPOCH FROM valid_time) / {gran_seconds})")
        select_fields.append("MIN(valid_time) AS t_0")
        if config['value']:
            alias = sql_alias(first_param.parametro)
            select_fields.append(
                f"ROUND({AGGREGATION_OPTIONS[first_param.aggregazione]}({config['value']})::NUMERIC,2) AS {alias}"
            )

            param_as.append(first_param.parametro)
            where_fields.append(f"ROUND({config['value']}::NUMERIC,2) IS NOT NULL")
            select_fields.append(f"(MIN(valid_time) + INTERVAL '{ow} hours') AS end_ow")

    else:
        time_col = "starttime" if first_param.tabella == "prescriptions" else "valid_time"

        select_fields.append(f"{time_col} AS t_0")
        group_fields.append(time_col)
        select_fields.append(f"({time_col} + INTERVAL '{ow} hours') AS end_ow")

        if first_param.tabella == "prescriptions":
            where_fields.append("starttime IS NOT NULL")

    # Assegnazione eventuale etichetta/descrizione al parametro
    if config["label"]:
        is_drug = config['label'] == "drug"
        label_alias = first_param.parametro if is_drug else config["label"]

        param_as.append(label_alias)
        select_fields.append(
            f"{config['label']} AS {sql_alias(first_param.parametro)}"
            if is_drug
            else config["label"]
        )
        group_fields.append(config["label"])

    param_as.append("t_0")

    field_str = ", ".join(select_fields)
    where_str = " AND ".join(where_fields)
    group_str = ", ".join(group_fields)

    # Assemblaggio del blocco SQL della prima CTE
    query = (
        f"WITH {NAME_VIEW[1]} AS (\n"
        f" SELECT {field_str}\n"
        f" FROM {C}{first_param.tabella}{f' {subname}' if first_param.tabella in ('labevents', 'prescriptions') else ''}\n"
        f"{f' INNER JOIN mimic_iv_2_2_untouched.icustays ic ON {subname}.hadm_id = ic.hadm_id\n' if first_param.tabella in ('labevents', 'prescriptions') else ''}"
        f" WHERE {where_str}\n"
        f" GROUP BY {group_str}\n"
        f"),\n"
    )

    return {NAME_VIEW[1]: param_as, "query": query}


def n_tmpv(idx: int, param: ParametroConfig, param_prec: ParametroConfig, ctePrec: str) -> dict:
    """
    Genera le CTE successive alla prima (dalla seconda in poi).

    Incrocia il parametro corrente con i dati della CTE precedente, verificando che la misurazione
    ricada nell'intervallo temporale valido [t_{idx-2}, end_ow].

    Args:
        idx: Indice d'ordine della vista (es. 2 per second_param).
        param: Parametro corrente da analizzare.
        param_prec: Parametro analizzato nel blocco precedente.
        ctePrec: Nome della CTE creata al passo precedente.
    """
    config = VIEW_CONFIG[param.tabella]
    config_prec = VIEW_CONFIG[param_prec.tabella]

    subname = "inp" if param.tabella.startswith("in") else param.tabella[0:2]

    join_fields = []
    select_fields = []
    param_as = []

    have_id = param.id is not None

    # Vincolo temporale: la nuova misurazione deve avvenire entro l'Observation Window stabilita
    where_fields = [
        f"{subname}.itemid = {param.id}" if have_id else f"{subname}.tipo = '{param.parametro}'",
        f"{subname}.valid_time BETWEEN f{idx - 1}.t_{idx - 2} AND f{idx - 1}.end_ow" if have_id
        else f"{subname}.starttime BETWEEN f{idx - 1}.t_{idx - 2} AND f{idx - 1}.end_ow"
    ]
    group_fields = []

    # Condizione di JOIN sulla chiave corretta (stay_id vs hadm_id)
    if (param_prec.tabella == "labevents" or param_prec.tabella == "prescriptions") and ctePrec == NAME_VIEW[1]:
        join_fields.append(f"f{idx - 1}.{config_prec['distinct']} = {subname}.{config_prec['distinct']}")
    else:
        join_fields.append(f"f{idx - 1}.{config['distinct']} = {subname}.{config['distinct']}")

    select_fields.append(f"f{idx - 1}.stay_id")
    select_fields.append(f"f{idx - 1}.hadm_id")
    select_fields.append(f"f{idx - 1}.end_ow")
    group_fields.append(f"f{idx - 1}.stay_id")
    group_fields.append(f"f{idx - 1}.hadm_id")
    group_fields.append(f"f{idx - 1}.end_ow")

    # Mantiene la memoria dei timestamp precedenti (t_0, t_1, ...)
    var = idx - 2
    while var >= 0:
        select_fields.append(f"f{idx - 1}.t_{var}")
        group_fields.append(f"f{idx - 1}.t_{var}")
        var -= 1

    # Applicazione dell'aggregazione per il parametro N-esimo
    if param.aggregazione and param.granularita:
        gran_hours = int(param.granularita.replace("h", ""))
        gran_seconds = gran_hours * 3600
        group_fields.append(
            f"FLOOR(EXTRACT(EPOCH FROM ({subname}.valid_time - f{idx - 1}.t_{idx - 2})) / {gran_seconds})")
        select_fields.append(f"MIN({subname}.valid_time) AS t_{idx - 1}")
        if config['value']:
            alias = sql_alias(param.parametro)
            select_fields.append(
                f"ROUND({AGGREGATION_OPTIONS[param.aggregazione]}({subname}.{config['value']})::NUMERIC,2) AS {alias}"
            )
            param_as.append(param.parametro)
            where_fields.append(f"ROUND({subname}.{config['value']}::NUMERIC,2) IS NOT NULL")
    else:
        time_col = "starttime" if param.tabella == "prescriptions" else "valid_time"

        select_fields.append(f"{subname}.{time_col} AS t_{idx - 1}")
        group_fields.append(f"{subname}.{time_col}")

        if param.tabella == "prescriptions":
            where_fields.append(f"{subname}.starttime IS NOT NULL")

    if config["label"]:
        is_drug = config['label'] == "drug"
        label_alias = param.parametro if is_drug else config["label"]

        param_as.append(f"{label_alias}")
        select_fields.append(
            f"{subname}.{config['label']} AS {sql_alias(param.parametro)}" if is_drug else f"{subname}.{config['label']}"
        )
        group_fields.append(f"{subname}.{config['label']}")

    param_as.append(f"t_{idx - 1}")

    field_str = ", ".join(select_fields)
    where_str = " AND ".join(where_fields)
    group_str = ", ".join(group_fields)
    join_str = "".join(join_fields)

    # Assemblaggio della CTE N-esima
    query = (
        f"{NAME_VIEW[idx]} AS (\n"
        f" SELECT {field_str}\n"
        f" FROM {C}{param.tabella} {subname}\n"
        f" INNER JOIN {ctePrec} f{idx - 1} ON {join_str}\n"
        f" WHERE {where_str}\n"
        f" GROUP BY {group_str}\n"
        f"),\n"
    )

    return {
        NAME_VIEW[idx]: param_as,
        "query": query,
    }


def final_query(diz: dict, ww: int, pw: int) -> str:
    """
    Costruisce la SELECT finale incrociando l'Observation Window con la tabella AKI.

    Verifica la presenza di insorgenza di AKI nella finestra di predizione (PW), 
    ovvero dopo un tempo di cuscinetto (WW - Warning Window) dal termine dell'OW.

    Args:
        diz: Dizionario contenente le CTE generate e i rispettivi campi esportati.
        ww: Warning Window in ore.
        pw: Prediction Window in ore.
    """
    select_fields = ["sp.subject_id"]
    order_fields = ["o.subject_id"]
    join_fields = []

    count = 1
    for key, value in diz.items():
        subname = f"f{count}"
        for val in value:
            select_fields.append(f"{subname}.{sql_alias(val)}")
            if val.startswith("t_"):
                order_fields.append(f"o.{val}")
        join_conditions = []
        var = count - 2
        while var >= 0:
            join_conditions.append(f"f{count}.t_{var} = f{count - 1}.t_{var}")
            var -= 1
        join_strs = " AND ".join(join_conditions)
        join_fields.append(
            f" INNER JOIN {key} f{count} ON sp.stay_id = f{count}.stay_id {f'AND {join_strs}' if count > 1 else ''}")
        count += 1

    field_str = ", ".join(select_fields)
    order_str = ", ".join(order_fields)
    join_str = "\n".join(join_fields)

    # Sostituisce i prefissi delle tabelle con l'alias della vista finale 'o'
    fields_str2 = re.sub(r"\b(f\d+|sp)\.", "o.", field_str)

    # Query finale: Unisce le finestre di osservazione valide con gli eventi AKI nell'intervallo (end_ow + ww, end_ow + ww + pw]
    query = (
        f"observation_window AS (\n"
        f" SELECT DISTINCT {field_str}, f{count - 1}.end_ow, f{count - 1}.hadm_id FROM stable_patient sp\n"
        f"{join_str}\n"
        f")\n"
        f"SELECT {fields_str2}, a.aki AS stage_aki, a.charttime AS t_stage_aki FROM aki a\n"
        f"INNER JOIN observation_window o ON (o.subject_id = a.subject_id AND a.hadm_id = o.hadm_id AND a.charttime > (o.end_ow + INTERVAL '{ww} hours')"
        f" AND a.charttime <= (o.end_ow + INTERVAL '{ww + pw} hours'))\n"
        f"ORDER BY {order_str}"
    )

    return query


def prediction_AKI(payload: PipelineInput) -> str:
    """
    Funzione principale (Orchestratore): accetta il payload di configurazione e concatena 
    le varie funzioni per restituire la query SQL completa ed eseguibile.
    """
    parameters = payload.parametri
    windows = payload.windows

    cte_params = {}

    # Genera la prima CTE
    first = first_tmpv(parameters[0], windows.ow)
    query = first["query"]
    cte_params[NAME_VIEW[1]] = first[NAME_VIEW[1]]

    cte_prec = NAME_VIEW[1]
    param_prec = parameters[0]

    # Cicla e genera tutte le CTE intermedie
    for idx, param in enumerate(parameters[1:], 1):
        n = n_tmpv(idx + 1, param, param_prec, cte_prec)
        query += n["query"]
        cte_params[NAME_VIEW[idx + 1]] = n[NAME_VIEW[idx + 1]]

        param_prec = parameters[idx]
        cte_prec = NAME_VIEW[idx + 1]

    # Concatena il blocco di chiusura e calcolo del target (AKI)
    query += final_query(cte_params, windows.ww, windows.pw)

    return query


def get_inputevents() -> str:
    """Restituisce la query per la lista degli eventi di input disponibili."""
    return "SELECT * FROM droplist_inputevents"


def kill_query(pid: int) -> str:
    """Genera la query SQL per annullare la query associata a uno specifico PID PostgreSQL."""
    return f"SELECT pg_cancel_backend({pid})"


def get_PID() -> str:
    """Restituisce la query SQL per ottenere il Process ID (PID) del backend di sessione."""
    return "SELECT pg_backend_pid()"