from backend.schema import PipelineInput, ParametroConfig

C = "v_"
NAME_VIEW =  {
    1 : "first_param",
    2 : "second_param",
    3 : "third_param",
    4 : "fourth_param",
    5 : "fifth_param",
    6 : "sixth_param",
}



VIEW_CONFIG = {
    "chartevents" : {
        "distinct" : "stay_id",
        "label" : "",
        "value" : "val"

    },
    "inputevents": {
        "distinct": "stay_id",
        "label" : "drug_name",
        "value" : ""

    },
    "labevents": {
        "distinct": "hadm_id",
        "label" : "",
        "value" : "val"

    },
    "outputevents": {
        "distinct": "stay_id",
        "label" : "",
        "value" : "val"

    },
    "procedureevents": {
        "distinct": "stay_id",
        "label" : "procedure_name",
        "value" : ""

    }
}

AGGREGATION_OPTIONS = {
    "Media" : "AVG",
    "Minimo" : "MIN",
    "Massimo" : "MAX"
}



def first_tmpv(first_param: ParametroConfig) :
    config = VIEW_CONFIG[first_param.tabella]

    param_as = []
    select_fields = []

    # Campo distinct
    if first_param.tabella != "labevents":
        select_fields.append("stay_id")
    select_fields.append("hadm_id")

    # Label facoltativa
    if config["label"]:
        select_fields.append(config["label"])

    # Calcolo tempi/valori se non c'è aggregazione
    if first_param.granularita is None and first_param.aggregazione is None:
        select_fields.append("valid_time AS t_0")
        if config["value"]:
            select_fields.append(f"{config["value"]} AS {first_param.parametro}")
            param_as.append(first_param.parametro)
        select_fields.append("(valid_time + INTERVAL '72 hours') AS end_ow")
    else:
        # Calcolo granularità in secondi
        gran_hours = int(first_param.granularita.replace("h", "")) if first_param.granularita else 1
        gran_seconds = gran_hours * 3600

        # Bucket temporale
        select_fields.append(
            f"FLOOR(EXTRACT(EPOCH FROM (valid_time - MIN(valid_time) OVER (PARTITION BY {config['distinct']}))) / {gran_seconds}) AS bucket_num"
        )
        param_as.append("bucket_num")
        # Tempo minimo del bucket
        select_fields.append("MIN(valid_time) AS t_0")

        # Aggregazione del valore
        if first_param.aggregazione and config["value"]:
            select_fields.append(
                f"{AGGREGATION_OPTIONS[first_param.aggregazione]}({config['value']}) AS {first_param.parametro}"
            )
            param_as.append(first_param.parametro)


    fields_str = ", ".join(select_fields)

    query = (
        f"WITH {NAME_VIEW[1]} AS (\n"
        f"  SELECT DISTINCT ON ({config['distinct']}) {fields_str}\n"
        f"  FROM {C}{first_param.tabella}\n"
        f"  WHERE item_id = {first_param.id}"
    )

    if config['value']:
        query += f" AND\n {config['value']} IS NOT NULL\n"

    if first_param.granularita is not None and first_param.aggregazione is not None:
        query += f"  GROUP BY {config['distinct']}, bucket_num\n"


    return  {
        "cte_name" : f"{C}{VIEW_CONFIG[first_param.tabella]}",
        "param_as" : param_as,
        "query" : query
    }




def n_tmpv(idx: int ,param: ParametroConfig) :
    subname = param.tabella[0:2]
    config = VIEW_CONFIG[param.tabella]
    select_fields = []
    param_as = []



    select_fields.append("f1.stay_id")


    if config['label']:
        select_fields.append(f"{config['label']}")

    if param.granularita is None and param.aggregazione is None:
        select_fields.append(f"valid_time AS t_{idx-1}")

        if config['value']:
            select_fields.append(f"{config['value']} AS {param.parametro}")
            param_as.append(param.parametro)
    else:
        gran_hours = int(param.granularita.replace("h", "")) if param.granularita else 1
        gran_seconds = gran_hours * 3600

        # Bucket temporale
        select_fields.append(
            f"FLOOR(EXTRACT(EPOCH FROM (valid_time - f1.t_0)) / {gran_seconds}) AS bucket_num"
        )
        param_as.append("bucket_num")
        # Tempo minimo del bucket
        select_fields.append(f"MIN(valid_time) AS t_{idx-1}")

        # Aggregazione del valore
        if param.aggregazione and config["value"]:
            select_fields.append(
                f"{AGGREGATION_OPTIONS[param.aggregazione]}({config['value']}) AS {param.parametro}"
            )
            param_as.append(param.parametro)

    fields_str = ", ".join(select_fields)

    query = (
        f"),\n{NAME_VIEW[idx]} AS (\n" 
        f"  SELECT {fields_str}\n"
        f"  FROM {C}{param.tabella} {subname}\n"
        f"  INNER JOIN first_param f1 ON f1.{config['distinct']} = {subname}.{config['distinct']}\n"
        f"  WHERE item_id = {param.id} AND\n"
        f"  {subname}.valid_time BETWEEN f1.t_0 AND f1.end_ow"
    )

    if config['value']:
        query += f" AND\n {config['value']} IS NOT NULL\n"

    if param.granularita is not None and param.aggregazione is not None:
        query += f"  GROUP BY f1.stay_id, bucket_num\n"



    return  {
        "cte_name" :  NAME_VIEW[idx],
        "param_as" : param_as,
        "query" : query,
    }



def final_query(param_as , ctes) -> str:
    pass


def prediction_AKI(payload: PipelineInput) :
    parameters = payload.parametri
    param_as = []
    ctes = []

    query = first_tmpv(parameters[0])["query"]
    param_as.extend(first_tmpv(parameters[0])["param_as"])
    ctes.extend(first_tmpv(parameters[0])["cte_name"])

    for idx,param in enumerate(parameters[1:], 1):
        query += n_tmpv(idx+1,param)["query"]
        param_as.extend(n_tmpv(idx + 1, param)["param_as"])
        ctes.extend(n_tmpv(idx+1,param)["cte_name"])
    query += ")\n"
    #query += final_query(param_as,ctes)

    return query

# ==========================================
# 3. MAIN DI TEST
# ==========================================
# 3. MAIN DI TEST SU TUTTE LE TABELLE
# ==========================================
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
                id=225798,
                parametro="dialysis_present"
            )
        ]
    )

    # Esecuzione
    sql_query = prediction_AKI(payload_test)

    # Stampa dei risultati
    print("--- QUERY GENERATA ---")
    print(sql_query)