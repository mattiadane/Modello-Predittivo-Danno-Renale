from typing import Any

from backend.schema import PipelineInput, ParametroConfig


def sql_alias(name: str) -> str:
    """
    Genera un alias SQL sicuro:
    - rimuove virgolette interne
    - mantiene spazi e caratteri speciali
    - racchiude tutto tra virgolette doppie
    """
    cleaned = name.replace('"', '').strip()
    return f"\"{cleaned}\""


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
        "label": "drug_name",
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


def first_tmpv(first_param: ParametroConfig):
    config = VIEW_CONFIG[first_param.tabella]
    gran_seconds = 0
    param_as = []
    select_fields = []

    # stay_id / hadm_id
    if first_param.tabella != "labevents":
        select_fields.append("stay_id")
    select_fields.append("hadm_id")

    # label opzionale
    if config["label"]:
        select_fields.append(config["label"])
        param_as.append(config["label"])

    # ============================================================
    # CASO 1 — SENZA GRANULARITÀ → PRIMA OCCORRENZA (DISTINCT ON)
    # ============================================================
    if first_param.granularita is None and first_param.aggregazione is None:

        select_fields.append("valid_time AS t_0")
        param_as.append("t_0")

        if config["value"]:
            alias = sql_alias(first_param.parametro)
            select_fields.append(f"{config['value']} AS {alias}")
            param_as.append(first_param.parametro)

        select_fields.append("(valid_time + INTERVAL '72 hours') AS end_ow")

        fields_str = ", ".join(select_fields)

        query = (
            f"WITH {NAME_VIEW[1]} AS (\n"
            f"  SELECT DISTINCT ON ({config['distinct']}) {fields_str}\n"
            f"  FROM {C}{first_param.tabella}\n"
            f"  WHERE itemid = {first_param.id} AND val IS NOT NULL\n"
            f"  ORDER BY {config['distinct']}, valid_time ASC\n"
            f")"
        )

        return {NAME_VIEW[1]: param_as, "query": query}

    # ============================================================
    # CASO 2 — CON GRANULARITÀ → SERVE IL GROUP BY
    # ============================================================
    else:
        gran_hours = int(first_param.granularita.replace("h", "")) if first_param.granularita else 1
        gran_seconds = gran_hours * 3600

        # bucket temporale corretto
        select_fields.append(
            f"FLOOR(EXTRACT(EPOCH FROM valid_time) / {gran_seconds}) AS bucket_num"
        )
        param_as.append("bucket_num")

        # t_0 = MIN(valid_time) del bucket
        select_fields.append("MIN(valid_time) AS t_0")
        param_as.append("t_0")

        # aggregazione del valore
        if first_param.aggregazione and config["value"]:
            alias = sql_alias(first_param.parametro)
            select_fields.append(
                f"{AGGREGATION_OPTIONS[first_param.aggregazione]}({config['value']}) AS {alias}"
            )
            param_as.append(first_param.parametro)

        # end_ow basato su t_0 aggregato
        select_fields.append("MIN(valid_time) + INTERVAL '72 hours' AS end_ow")

        fields_str = ", ".join(select_fields)

        query = (
            f"WITH {NAME_VIEW[1]} AS (\n"
            f"  SELECT {fields_str}\n"
            f"  FROM {C}{first_param.tabella}\n"
            f"  WHERE itemid = {first_param.id} AND val IS NOT NULL\n"
        )
        query += f"  GROUP BY {config['distinct']},"
        if first_param.tabella != "labevents":
            query += f"hadm_id,"
        query += f"  FLOOR(EXTRACT(EPOCH FROM valid_time) / {gran_seconds})\n"


        return {NAME_VIEW[1]: param_as, "query": query}


def n_tmpv(idx: int, param: ParametroConfig):
    subname = param.tabella[0:2]
    if subname == "in":
        subname = "inp"

    config = VIEW_CONFIG[param.tabella]
    select_fields = []
    param_as = []
    gran_seconds = 0

    select_fields.append("f1.stay_id")

    if param.granularita is None and param.aggregazione is None:
        select_fields.append(f"{subname}.valid_time AS t_{idx-1}")
        param_as.append(f"t_{idx-1}")

        if config['value']:
            alias = sql_alias(param.parametro)
            select_fields.append(f"{subname}.{config['value']} AS {alias}")
            param_as.append(param.parametro)

    else:
        gran_hours = int(param.granularita.replace("h", "")) if param.granularita else 1
        gran_seconds = gran_hours * 3600

        select_fields.append(
            f"FLOOR(EXTRACT(EPOCH FROM ({subname}.valid_time - f1.t_0)) / {gran_seconds}) AS bucket_num"
        )
        param_as.append("bucket_num")

        select_fields.append(f"MIN({subname}.valid_time) AS t_{idx-1}")
        param_as.append(f"t_{idx-1}")

        if param.aggregazione and config["value"]:
            alias = sql_alias(param.parametro)
            select_fields.append(
                f"{AGGREGATION_OPTIONS[param.aggregazione]}({subname}.{config['value']}) AS {alias}"
            )
            param_as.append(param.parametro)

    if config['label']:
        select_fields.append(f"{subname}.{config['label']}")
        param_as.append(config["label"])

    fields_str = ", ".join(select_fields)

    query = (
        f"),\n{NAME_VIEW[idx]} AS (\n"
        f"  SELECT {fields_str}\n"
        f"  FROM {C}{param.tabella} {subname}\n"
        f"  INNER JOIN first_param f1 ON f1.{config['distinct']} = {subname}.{config['distinct']}\n"
        f"  WHERE {subname}.itemid = {param.id} AND\n"
        f"  {subname}.valid_time BETWEEN f1.t_0 AND f1.end_ow"
    )

    if config['value']:
        query += f" AND\n  {subname}.{config['value']} IS NOT NULL\n"

    if param.granularita and param.aggregazione:
        query += (
            f"  GROUP BY f1.stay_id, "
            f"FLOOR(EXTRACT(EPOCH FROM ({subname}.valid_time - f1.t_0)) / {gran_seconds})\n"
        )

    return {
        NAME_VIEW[idx]: param_as,
        "query": query,
    }


def final_query(dict) -> str:
    select_fields = ["sp.subject_id"]
    where_fields = []

    count = 1
    for key, value in dict.items():
        subname = f"f{count}"
        for val in value:
            if val == "bucket_num":
                continue
            select_fields.append(f"{subname}.{sql_alias(val)}")
        count += 1

    field_str = ", ".join(select_fields)

    query = f"SELECT {field_str} FROM stable_patient sp\n"

    count = 1
    prec_key = "sp"
    for key in dict.keys():
        if prec_key != "sp":
            query += (
                f"INNER JOIN {key} f{count} ON (f{count}.stay_id = f{count - 1}.stay_id"
            )
            if "bucket_num" in dict[key] and "bucket_num" in dict[prec_key]:
                query += f" AND {key}.bucket_num = {prec_key}.bucket_num"
            query += ")\n"
        else:
            query += f"INNER JOIN {key} f{count} ON (sp.stay_id = f{count}.stay_id)\n"

        prec_key = key
        count += 1

    for i in range(1, len(dict.keys())):
        where_fields.append(f" f{i+1}.t_{i} > f{i}.t_{i-1}")

    where_fields = " AND ".join(where_fields)

    query += f"WHERE {where_fields}\nORDER BY sp.subject_id"
    return query


def prediction_AKI(payload: PipelineInput):
    parameters = payload.parametri
    cte_params = {}

    query = first_tmpv(parameters[0])["query"]
    cte_params[NAME_VIEW[1]] = first_tmpv(parameters[0])[NAME_VIEW[1]]

    for idx, param in enumerate(parameters[1:], 1):
        query += n_tmpv(idx + 1, param)["query"]
        cte_params[NAME_VIEW[idx + 1]] = n_tmpv(idx + 1, param)[NAME_VIEW[idx + 1]]

    query += "\n)\n"
    query += final_query(cte_params)


'''
if __name__ == "__main__":
    print("=== TEST GENERAZIONE QUERY AKI ===\n")

    # Creazione di un payload di test con vari scenari
    payload_test = PipelineInput(
        parametri=[
            # Primo parametro (senza aggregazione)
            ParametroConfig(
                tabella="chartevents",
                id=220045,
                parametro="heart_rate"
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
            ParametroConfig(
                tabella="procedureevents",
                id=224275,
                parametro="dialysis_present"
            )
        ]
    )

    # Esecuzione
    sql_query = prediction_AKI(payload_test)

    # Stampa dei risultati
    print("--- QUERY GENERATA ---")
    print(sql_query)
'''