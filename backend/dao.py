from backend.schema import PipelineInput, ParametroConfig, WindowsConfig

C = "v_"
NAME_VIEW = {
    1: "first_param",
    2: "second_param",
    3: "third_param",
    4: "fourth_param",
    5: "fifth_param",
    6: "sixth_param",
}

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

AGGREGATION_OPTIONS = {
    "Media": "AVG",
    "Minimo": "MIN",
    "Massimo": "MAX"
}


def sql_alias(name: str) -> str:
    cleaned = name.replace('"', '').strip()
    return f"\"{cleaned}\""


def first_tmpv(first_param: ParametroConfig, windows: WindowsConfig):
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


    # stay_id / hadm_id
    if first_param.tabella not in ("labevents", "prescriptions"):
        select_fields.append("stay_id")
        group_fields.append("stay_id")
        param_as.append("stay_id")
        select_fields.append("hadm_id")
        group_fields.append("hadm_id")
    else :
        subname = first_param.tabella[0:2]
        select_fields.append("ic.stay_id")
        group_fields.append("ic.stay_id")
        param_as.append("stay_id")
        select_fields.append("ic.hadm_id")
        group_fields.append("ic.hadm_id")
        where_fields.append(f"starttime BETWEEN ic.intime and ic.outtime")





    if first_param.aggregazione and first_param.granularita:
        gran_hours = int(first_param.granularita.replace("h", ""))
        gran_seconds = gran_hours * 3600

        group_fields.append(f"FLOOR(EXTRACT(EPOCH FROM valid_time) / {gran_seconds})")
        select_fields.append("MIN(valid_time) AS t_0")

        if config['value']:
            alias = sql_alias(first_param.parametro)
            select_fields.append(
                f"{AGGREGATION_OPTIONS[first_param.aggregazione]}({config['value']}) AS {alias}"
            )
            param_as.append(first_param.parametro)
            where_fields.append(f"{config['value']} IS NOT NULL")
            select_fields.append(f"(MIN(valid_time) + INTERVAL '{windows.ow} hours') AS end_ow")

    else:
        time_col = "starttime" if first_param.tabella == "prescriptions" else "valid_time"

        select_fields.append(f"{time_col} AS t_0")
        group_fields.append(time_col)
        select_fields.append(f"({time_col} + INTERVAL '{windows.ow} hours') AS end_ow")

        if first_param.tabella == "prescriptions":
            where_fields.append("starttime IS NOT NULL")

    # label opzionale
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

    query = (
        f"WITH {NAME_VIEW[1]} AS (\n"
        f" SELECT {field_str}\n"
        f" FROM {C}{first_param.tabella}{f' {subname}' if first_param.tabella in ('labevents', 'prescriptions') else ''}\n"
        f"{f' INNER JOIN mimic_iv_2_2_untouched.icustays ic ON {subname}.hadm_id = ic.hadm_id' if first_param.tabella in ('labevents', 'prescriptions') else ''}\n"
        f" WHERE {where_str}\n"
        f" GROUP BY {group_str}\n"
        f")"
    )

    return {NAME_VIEW[1]: param_as, "query": query}


def n_tmpv(idx: int, param: ParametroConfig, param_prec: ParametroConfig, ctePrec: str):
    config = VIEW_CONFIG[param.tabella]

    config_prec = VIEW_CONFIG[param_prec.tabella]

    subname = "inp" if param.tabella.startswith("in") else param.tabella[0:2]

    join_fields = []
    select_fields = []
    param_as = []

    have_id = param.id is not None
    where_fields = [
        f"{subname}.itemid = {param.id}" if have_id  else f"{subname}.tipo = '{param.parametro}'",
        f"{subname}.valid_time BETWEEN f{idx - 1}.t_{idx - 2} AND f{idx - 1}.end_ow" if have_id
        else f"{subname}.starttime BETWEEN f{idx - 1}.t_{idx - 2} AND f{idx - 1}.end_ow"
    ]
    group_fields = []

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

    var = idx - 2

    while var >= 0:
        select_fields.append(f"f{idx - 1}.t_{var}")
        group_fields.append(f"f{idx - 1}.t_{var}")
        var -= 1

    if param.aggregazione and param.granularita:
        # granularità → bucket temporale
        gran_hours = int(param.granularita.replace("h", ""))
        gran_seconds = gran_hours * 3600
        group_fields.append(
            f"FLOOR(EXTRACT(EPOCH FROM ({subname}.valid_time - f{idx - 1}.t_{idx - 2})) / {gran_seconds})")
        select_fields.append(f"MIN({subname}.valid_time) AS t_{idx - 1}")
        if config['value']:
            alias = sql_alias(param.parametro)
            select_fields.append(
                f"{AGGREGATION_OPTIONS[param.aggregazione]}({subname}.{config['value']}) AS {alias}"
            )
            param_as.append(param.parametro)
            where_fields.append(f"{subname}.{config['value']} IS NOT NULL")
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

    query = (
        f",\n{NAME_VIEW[idx]} AS (\n"
        f" SELECT {field_str}\n"
        f" FROM {C}{param.tabella} {subname}\n"
        f" INNER JOIN {ctePrec} f{idx - 1} ON {join_str}\n"
        f" WHERE {where_str}\n"
        f" GROUP BY {group_str}\n"
        f")"
    )

    return {
        NAME_VIEW[idx]: param_as,
        "query": query,
    }


def final_query(diz) -> str:
    select_fields = ["sp.subject_id"]
    join_fields = []
    order_fields = ["sp.subject_id"]

    count = 1
    for key, value in diz.items():
        subname = f"f{count}"
        for val in value:
            if val.startswith("t_"):
                order_fields.append(f"{subname}.{val}")
            select_fields.append(f"{subname}.{sql_alias(val)}")
        if count == 1:
            if "stay_id" in value:
                join_fields.append(f"INNER JOIN {key} f{count} ON sp.stay_id = f{count}.stay_id")
            else:
                join_fields.append(f"INNER JOIN {key} f{count} ON sp.hadm_id = f{count}.hadm_id")


        else:
            join_conditions = []
            var = count - 2
            while var >= 0:
                join_conditions.append(f"f{count}.t_{var} = f{count - 1}.t_{var}")
                var -= 1
            join_strs = " AND ".join(join_conditions)
            join_fields.append(f"INNER JOIN {key} f{count} ON sp.stay_id = f{count}.stay_id AND {join_strs}")
        count += 1

    field_str = ", ".join(select_fields)
    order_str = ", ".join(order_fields)
    join_str = "\n".join(join_fields)

    query = (
        f"SELECT DISTINCT {field_str} FROM stable_patient sp\n"
        f"{join_str}\n"
        f"ORDER BY {order_str}\n"
    )

    return query


def prediction_AKI(payload: PipelineInput):
    parameters = payload.parametri
    windows = payload.windows

    cte_params = {}

    first = first_tmpv(parameters[0], windows)
    query = first["query"]
    cte_params[NAME_VIEW[1]] = first[NAME_VIEW[1]]

    cte_prec = NAME_VIEW[1]
    param_prec = parameters[0]
    for idx, param in enumerate(parameters[1:], 1):
        n = n_tmpv(idx + 1, param, param_prec, cte_prec)
        query += n["query"]
        cte_params[NAME_VIEW[idx + 1]] = n[NAME_VIEW[idx + 1]]

        param_prec = parameters[idx]
        cte_prec = NAME_VIEW[idx + 1]

    query += "\n"
    query += final_query(cte_params)

    return query


def get_inputevents():
    return "SELECT * FROM droplist_inputevents"


def kill_query(pid):
    return f"SELECT pg_cancel_backend({pid})"


def get_PID():
    return "SELECT pg_backend_pid()"


'''if __name__ == "__main__":
    print("=== TEST GENERAZIONE QUERY AKI ===\n")

    # Creazione di un payload di test con vari scenari
    payload_test = PipelineInput(
        windows=
        WindowsConfig(
            ow=12,
            pw=12,
            ww=12
        ),
        parametri=[
            ParametroConfig(
                tabella="prescriptions",
                id=None,
                parametro="Diuretico",
                granularita=None,
                aggregazione=None
            ),
            # Primo parametro (senza aggregazione)
            ParametroConfig(
                tabella="chartevents",
                id=220045,
                parametro="heart_rate",
                granularita="6h",
                aggregazione="Media"
            ),

            ParametroConfig(
                tabella="inputevents",
                id=224275,
                parametro="dialysis_present",
                granularita="6h",
                aggregazione="Media"
            ),

            ParametroConfig(
                tabella="procedureevents",
                id=224275,
                parametro="dialysis_present",
                granularita=None,
                aggregazione=None
            ),

            # Secondo parametro (con aggregazione e granularità)
            ParametroConfig(
                tabella="labevents",
                id=50912,
                parametro="creatinine",
                granularita="6h",
                aggregazione="Media"
            ),
            # Terzo parametro (con valore non aggregato)

        ]
    )

    # Esecuzione
    sql_query = prediction_AKI(payload_test)

    # Stampa dei risultati
    print("--- QUERY GENERATA ---")
    print(sql_query)
'''
