from backend.schema import PipelineInput, ParametroConfig

C = "v_"
NAME_VIEW =  {
    1 : "firt_param",
    2 : "second_param",
    3 : "third_param",
    4 : "fourth_param",
    5 : "fifth_param",
    6 : "sixth_param",
}


VIEW_CONFIG = {
    "chartevents" : {
        "distinct" : "stay_id",

    },
    "inputevents": {
        "distinct": "stay_id",

    },
    "labevents": {
        "distinct": "hadm_id",

    },
    "outputevents": {
        "distinct": "stay_id",

    },
    "procedureevents": {
        "distinct": "stay_id",

    }
}



def prediction_AKI(payload : PipelineInput) :
    parameters = payload.parametri
    query = first_tmpv(parameters[0])





    return query

def first_tmpv(first_param : ParametroConfig):

    query = f"WITH {NAME_VIEW[1]} AS ("


    return query + ")"


def n_tmpview():
    pass