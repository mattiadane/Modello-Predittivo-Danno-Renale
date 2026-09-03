import os
import pandas as pd
import requests
import streamlit as st



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


GROUP_TABLE = ["chartevents", "labevents", "outputevents"]



DRUG_GROUPS = ["Nefrotossici","Diuretici","Antipertensivi","Chemioterapici","Fans","Dopamine"]

GRANULARITY_OPTIONS = {
    "1 ora": "1h",
    "3 ore": "3h",
    "6 ore": "6h",
}

AGGREGATION_OPTIONS = ["Media", "Minimo", "Massimo"]


# Con questo metodo vengono caricati i dati csv una singola volta
@st.cache_data
def open_csv(filename: str) -> pd.DataFrame:
    """Carica un file CSV dalla cartella data se esiste."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path).dropna(how="all")
    return pd.DataFrame(columns=["itemid", "label"])

# COn questo metodo viene fatta la richiesta API per popolare la lista degli input events una singola volta
@st.cache_data
def fetch_inputevents() -> pd.DataFrame:
    """Recupera gli inputevents dall'API e li salva in cache."""
    try:
        response = requests.get("http://127.0.0.1:8000/inputevents")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Errore nel recupero dati dall'API: {e}")

    return pd.DataFrame(columns=["itemid", "label"])


def local_css(file_name: str):
    """Carica eventuali stili CSS personalizzati."""
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def extract_selected_items(df: pd.DataFrame, selected_labels: list, table_name: str) -> list:
    """Estrae locale dei dizionari con la mappa completa dei parametri."""
    filtered_df = df[df["label"].isin(selected_labels)]
    return [
        {
            "tabella": table_name,
            "id": int(row["itemid"]),
            "parametro": str(row["label"]),
            "granularita": None,
            "aggregazione": None
        }
        for _, row in filtered_df.iterrows()
    ]


def create_map_for_drugs(type_drug : str) -> dict:
    return {
        "tabella" : "prescription",
        "id" : None,
        "parametro" : type_drug,
        "granularita": None,
        "aggregazione": None
    }


# --- SEZIONI UI ---
def render_farmaci() -> list:
    """Renderizza la selezione farmaci e restituisce in locale le macrocategorie scelte."""
    with st.container(border=True):
        st.markdown("### Farmaci")
        col1, col2, col3 = st.columns(3)

        with col1:
            drug_nephro = st.checkbox("Nefrotossici", key="Nefrotossici")
            drug_diuretic = st.checkbox("Diuretici", key="Diuretici")
        with col2:
            drug_antihyp = st.checkbox("Antipertensivi", key="Antipertensivi")
            drug_chemio = st.checkbox("Chemioterapici",key="Chemioterapici")
        with col3:
            drug_fans = st.checkbox("Fans",key="Fans")
            drug_dopa = st.checkbox("Dopamine", key="Dopamine")

        selected_drug_groups =  []
        if drug_nephro:
            selected_drug_groups.append(create_map_for_drugs("Nefrotossico"))
        if drug_diuretic:
            selected_drug_groups.append(create_map_for_drugs("Diuretico"))
        if drug_antihyp:
            selected_drug_groups.append(create_map_for_drugs("Antipertensivo"))
        if drug_chemio:
            selected_drug_groups.append(create_map_for_drugs("Chemioterapico"))
        if drug_fans:
            selected_drug_groups.append(create_map_for_drugs("Fans"))
        if drug_dopa:
            selected_drug_groups.append(create_map_for_drugs("Dopamina"))

        return selected_drug_groups

def render_multiselect(selected_drugs: list) -> list:
    """
    Renderizza i multiselect per gli eventi clinici.
    Restituisce in locale:
    1. La lista delle opzioni selezionate (nomi)
    2. La lista degli oggetti evento estratti
    """
    with st.container(border=True):
        st.markdown("### Eventi Clinici")
        col1, col2, col3 = st.columns(3)


        chartevents_df = open_csv("first200chartevents.csv")
        outputevents_df = open_csv("outputevents.csv")

        inputevents_df = fetch_inputevents()

        procedures_df = open_csv("first200procedures.csv")
        labevents_df = open_csv("first200labevents.csv")


        all_events_objects = list(selected_drugs)


        with col1:
            labels_chart = st.multiselect("Chartevents", chartevents_df["label"].tolist(), key="ms_chart")
            all_events_objects.extend(extract_selected_items(chartevents_df, labels_chart, "chartevents"))

            labels_input = st.multiselect("Inputevents",inputevents_df["label"].tolist(), key="ms_input")
            all_events_objects.extend(extract_selected_items(inputevents_df, labels_input, "inputevents"))

        with col2:
            labels_output = st.multiselect("Outputevents", outputevents_df["label"].tolist(), key="ms_output")
            all_events_objects.extend(extract_selected_items(outputevents_df, labels_output, "outputevents"))

        with col3:
            labels_lab = st.multiselect("Labevents", labevents_df["label"].tolist(), key="ms_lab")
            all_events_objects.extend(extract_selected_items(labevents_df, labels_lab, "labevents"))

            labels_proc = st.multiselect("Procedures", procedures_df["label"].tolist(), key="ms_proc")
            all_events_objects.extend(extract_selected_items(procedures_df, labels_proc, "procedureevents"))

        return  all_events_objects

def render_window() -> dict:


    with st.container(border=True):
        st.markdown("### Dimensioni finestre")
        col1, col2, col3 = st.columns(3)

        with col1 :
            ow = st.number_input(
                "Dimensione Observation Window",
                min_value=1,
                step=1
            )
        with col2 :
            ww = st.number_input(
                "Dimensione Waiting Window",
                min_value=0,
                step=1
            )
        with col3 :
            pw = st.number_input(
                "Dimensione Prediction Window",
                min_value=1,
                step=1
            )

    return {
        "ow": ow,
        "ww": ww,
        "pw": pw,
    }

def check_granularity(object_events) -> dict | None:
    """Mostra la configurazione di granularità se è stato selezionato almeno un parametro tra chartevents, labevents,outputevents"""


    if not any(event.get("tabella") in GROUP_TABLE  for event in object_events):
        return None

    with st.container(border=True):
        st.markdown("### Configurazione Parametri:")
        col_g, col_a = st.columns(2)
        with col_g:
            gran_label = st.selectbox(
                "Granularità",
                options=list(GRANULARITY_OPTIONS.keys()),
                index=2,
                key="sb_gran",
            )
        with col_a:
            agg_label = st.selectbox(
                "Aggregazione",
                options=AGGREGATION_OPTIONS,
                index=0,
                key="sb_agg"
            )

    return {
        "granularita": GRANULARITY_OPTIONS[gran_label],
        "aggregazione": agg_label
    }


def render_ordering_section(events_objects: list, granularity_info: dict | None,windows_info: dict ) :
    """
    Costruisce l'interfaccia di riordino e salva DIRETTAMENTE in st.session_state['pipeline_input']
    l'unico array finale completo
    """

    # Mappa veloce locale: Nome Parametro -> Oggetto Evento
    item_lookup_map = {item["parametro"]: item for item in events_objects}
    current_keys = list(item_lookup_map.keys())

    if not current_keys:
        st.session_state["pipeline_input"] = []
        st.session_state["feature_sorter"] = []
        st.session_state["prev_current_keys"] = []
        return

        # Inizializzazione dello stato al primo avvio
    if "feature_sorter" not in st.session_state:
        st.session_state["feature_sorter"] = current_keys
        st.session_state["prev_current_keys"] = current_keys
    else:
        prev_keys = st.session_state.get("prev_current_keys", [])


        brand_new_keys = [k for k in current_keys if k not in prev_keys]

        current_sorter = [k for k in st.session_state["feature_sorter"] if k in current_keys]

        st.session_state["feature_sorter"] = current_sorter + brand_new_keys

        st.session_state["prev_current_keys"] = current_keys

    with st.container(border=True):
        st.markdown("### Ordina le tue Feature (Macro-Farmaci ed Eventi)")
        st.info("Rimuovi le voci con la 'x' e rinseriscile una ad una nell'ordine desiderato.")

        ordered_labels = st.multiselect(
            "Seleziona o reinserisci nell'ordine desiderato:",
            options=current_keys,
            key="feature_sorter"
        )


        # Costruzione dell'UNICO array che servirà al backend
        final_ordered_features = []
        for label in ordered_labels:


            feature_data = item_lookup_map[label].copy()


            if granularity_info and item_lookup_map[label]["tabella"] in GROUP_TABLE:
                feature_data["granularita"] = granularity_info["granularita"]
                feature_data["aggregazione"] = granularity_info["aggregazione"]
            final_ordered_features.append(feature_data)

        # SALVIAMO UNICAMENTE L'ARRAY FINALE PER IL BACKEND
        st.session_state["pipeline_input"] = {
            "windows" : windows_info,
            "features" : final_ordered_features
        }

        if ordered_labels:
            st.markdown("**Ordine finale per l'addestramento:**")
            st.caption(" → ".join([f"`{label}`" for label in ordered_labels]))


def render_button():
    """Pulsante per procedere alla pagina dei risultati."""
    st.write("")
    _, col_c, _ = st.columns([1, 1, 1])

    with col_c:
        if st.button("Elabora Modello",width='stretch', type="primary"):
            pipeline_data = st.session_state.get("pipeline_input", [])

            if not pipeline_data or (len(pipeline_data["features"]) < 3 or len(pipeline_data["features"]) > 6):
                st.warning("Seleziona dai 3 ai 6 parametri")
                return

            st.switch_page("pages/result.py")


# --- FLUSSO PRINCIPALE ---
local_css("frontend/style/style.css")

st.title("🩺 Prediction of Kidney Injury")

# Passaggio dati puramente in locale tra le funzioni:
selected_drugs = render_farmaci()
events_objects = render_multiselect(selected_drugs)

windows = render_window()

granularity_info = check_granularity(events_objects)

# Assembly finale direttamente in session_state['pipeline_input']
render_ordering_section(events_objects, granularity_info,windows)
render_button()