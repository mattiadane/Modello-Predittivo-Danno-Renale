from sqlalchemy.sql.util import join_condition

from backend.schema import PipelineInput, ParametroConfig

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

    param_as = []
    select_fields = []
    where_fields = [f"itemid = {first_param.id}"]
    group_fields = []

    # stay_id / hadm_id
    if first_param.tabella != "labevents":
        select_fields.append("stay_id")
        group_fields.append("stay_id")
    select_fields.append("hadm_id")
    group_fields.append("hadm_id")



    gran_hours = int(first_param.granularita.replace("h", "")) if first_param.granularita else 1
    gran_seconds = gran_hours * 3600

    group_fields.append(f"FLOOR(EXTRACT(EPOCH FROM valid_time) / {gran_seconds})")

    select_fields.append("MIN(valid_time) AS t_0")
    param_as.append("t_0")

    select_fields.append("(MIN(valid_time) + INTERVAL '72 hours') AS end_ow")

    # label opzionale
    if config["label"]:
        select_fields.append(config["label"])
        param_as.append(config["label"])
        group_fields.append(config["label"])

    if first_param.aggregazione and config["value"]:
        alias = sql_alias(first_param.parametro)
        select_fields.append(
            f"{AGGREGATION_OPTIONS[first_param.aggregazione]}({config['value']}) AS {alias}"
        )
        param_as.append(first_param.parametro)
        where_fields.append(f"{config['value']} IS NOT NULL")


    field_str = ", ".join(select_fields)
    where_str = " AND ".join(where_fields)
    group_str = ", ".join(group_fields)

    query = (
        f"WITH {NAME_VIEW[1]} AS (\n"
        f" SELECT {field_str}\n"
        f" FROM {C}{first_param.tabella}\n"
        f" WHERE {where_str}\n"
        f" GROUP BY {group_str}\n"
        f")"
    )


    return {NAME_VIEW[1]: param_as, "query": query}

def n_tmpv(idx: int, param: ParametroConfig, paramPrec: str):
    config = VIEW_CONFIG[param.tabella]


    subname = param.tabella[0:2]
    if subname == "in":
        subname = "inp"

    select_fields = []
    param_as = []
    where_fields = [
        f"{subname}.itemid = {param.id}",
        f"{subname}.valid_time BETWEEN f{idx-1}.t_{idx-2} AND f{idx-1}.end_ow"
    ]
    group_fields = []



    select_fields.append(f"f{idx-1}.stay_id")
    select_fields.append(f"f{idx - 1}.hadm_id")
    select_fields.append(f"f{idx-1}.end_ow")
    group_fields.append(f"f{idx-1}.end_ow")
    group_fields.append(f"f{idx-1}.stay_id")
    group_fields.append(f"f{idx - 1}.hadm_id")


    var = idx-2

    while var >= 0:
        select_fields.append(f"f{idx-1}.t_{var}")
        group_fields.append(f"f{idx-1}.t_{var}")
        var -= 1



    # granularità → bucket temporale
    gran_hours = int(param.granularita.replace("h", "")) if param.granularita else 1
    gran_seconds = gran_hours * 3600

    group_fields.append(f"FLOOR(EXTRACT(EPOCH FROM {subname}.valid_time) / {gran_seconds})")


    # tempo minimo del bucket
    select_fields.append(f"MIN({subname}.valid_time) AS t_{idx-1}")
    param_as.append(f"t_{idx-1}")




    if config["label"]:
        select_fields.append(f"{subname}.{config['label']}")
        param_as.append(config["label"])
        group_fields.append(f"{subname}.{config['label']}")


    # aggregazione
    if param.aggregazione and config["value"]:
        alias = sql_alias(param.parametro)
        select_fields.append(
            f"{AGGREGATION_OPTIONS[param.aggregazione]}({subname}.{config['value']}) AS {alias}"
        )
        param_as.append(param.parametro)
        where_fields.append(f"{subname}.{config['value']} IS NOT NULL")

    field_str = ", ".join(select_fields)
    where_str = " AND ".join(where_fields)
    group_str = ", ".join(group_fields)

    query = (
        f",\n{NAME_VIEW[idx]} AS (\n"
        f" SELECT {field_str}\n"
        f" FROM {C}{param.tabella} {subname}\n"
        f" INNER JOIN {paramPrec} f{idx-1} ON f{idx-1}.{config['distinct']} = {subname}.{config['distinct']}\n"
        f" WHERE {where_str}\n"
        f" GROUP BY {group_str}\n"
        f")"
    )

    return {
        NAME_VIEW[idx]: param_as,
        "query": query,
    }



def final_query(dict,limit : int = 50,offset : int = 0) -> str:
    select_fields = ["sp.subject_id"]
    join_fields = []

    count = 1
    for key, value in dict.items():
        subname = f"f{count}"
        for val in value:
            select_fields.append(f"{subname}.{sql_alias(val)}")
        if count == 1:
            join_fields.append(f"INNER JOIN {key} f{count} ON sp.stay_id = f{count}.stay_id")
        else :
            join_conditions = []
            var = count - 2
            while var >= 0:
                join_conditions.append(f"f{count}.t_{var} = f{count-1}.t_{var}")
                var -= 1
            join_strs = " AND ".join(join_conditions)
            join_fields.append(f"INNER JOIN {key} f{count} ON sp.stay_id = f{count}.stay_id AND {join_strs}")
        count += 1


    field_str = ", ".join(select_fields)

    join_str = "\n".join(join_fields)


    query = (
        f"SELECT DISTINCT {field_str} FROM stable_patient sp\n"
        f"{join_str}\n"
        f"ORDER BY sp.subject_id\nLIMIT {limit} OFFSET {offset}"
    )

    return query


def prediction_AKI(payload: PipelineInput,limit = 50, offset = 0):
    parameters = payload.parametri
    cte_params = {}

    query = first_tmpv(parameters[0])["query"]
    cte_params[NAME_VIEW[1]] = first_tmpv(parameters[0])[NAME_VIEW[1]]

    param_prec = NAME_VIEW[1]
    for idx, param in enumerate(parameters[1:], 1):
        query += n_tmpv(idx + 1, param,param_prec)["query"]
        cte_params[NAME_VIEW[idx + 1]] = n_tmpv(idx + 1, param,param_prec)[NAME_VIEW[idx + 1]]
        param_prec = NAME_VIEW[idx+1]

    query += "\n"
    query += final_query(cte_params,limit,offset)

    return query



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
                parametro="heart_rate",
                granularita="6h",
                aggregazione="Media"
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
                parametro="dialysis_present",
                granularita="6h",
                aggregazione="Media"
            )
        ]
    )

    # Esecuzione
    sql_query = prediction_AKI(payload_test)

    # Stampa dei risultati
    print("--- QUERY GENERATA ---")
    print(sql_query)
    
'''

