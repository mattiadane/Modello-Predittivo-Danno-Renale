import os
import pandas as pd
import requests
import streamlit as st

# --- Configurazione Percorsi e Costanti ---
# Individua la cartella root del progetto e il percorso della directory dei dati 'data'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Tabelle cliniche che supportano la configurazione di granularità temporale e aggregazione
GROUP_TABLE = ["chartevents", "labevents", "outputevents"]

# Categorie di farmaci disponibili per l'analisi
DRUG_GROUPS = ["Nefrotossici", "Diuretici", "Antipertensivi", "Chemioterapici", "Fans", "Dopamine"]

# Mappatura delle opzioni di granularità (interfaccia utente -> formato API/Backend)
GRANULARITY_OPTIONS = {
    "1 ora": "1h",
    "3 ore": "3h",
    "6 ore": "6h",
}

# Funzioni di aggregazione selezionabili per i dati delle tabelle cliniche
AGGREGATION_OPTIONS = ["Media", "Minimo", "Massimo"]


# --- Gestione Caching e Sorgenti Dati ---
@st.cache_data
def open_csv(filename: str) -> pd.DataFrame:
    """Carica un file CSV dalla directory 'data' mantenendolo in memoria cache.

    Rimuove le righe completamente vuote ed evita letture ridondanti su disco.
    """
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path).dropna(how="all")
    return pd.DataFrame(columns=["itemid", "label"])


@st.cache_data
def fetch_inputevents() -> pd.DataFrame:
    """Interroga l'API REST per recuperare la lista aggiornata degli inputevents.

    Sfrutta la cache di Streamlit per eseguire la chiamata HTTP una sola volta.
    """
    try:
        response = requests.get("http://127.0.0.1:8000/inputevents")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Errore nel recupero dati dall'API: {e}")

    return pd.DataFrame(columns=["itemid", "label"])


def local_css(file_name: str):
    """Inietta un file CSS personalizzato all'interno dell'interfaccia Streamlit."""
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


# --- Helper per la Strutturazione dei Dati ---
def extract_selected_items(df: pd.DataFrame, selected_labels: list, table_name: str) -> list:
    """Filtra un DataFrame in base alle etichette selezionate dall'utente.

    Trasforma i dati in una lista di dizionari formattati per il payload della pipeline.
    """
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


def create_map_for_drugs(type_drug: str) -> dict:
    """Crea la struttura dati standardizzata per una categoria di farmaci selezionata."""
    return {
        "tabella": "prescriptions",
        "id": None,
        "parametro": type_drug,
        "granularita": None,
        "aggregazione": None
    }


# --- Componenti Interfaccia Utente (UI) ---
def render_farmaci() -> list:
    """Renderizza i checkbox delle macrocategorie di farmaci nella UI.

    Ritorna la lista dei dizionari corrispondenti alle categorie selezionate.
    """
    with st.container(border=True):
        st.markdown("### Farmaci")
        col1, col2, col3 = st.columns(3)

        with col1:
            drug_nephro = st.checkbox("Nefrotossici", key="Nefrotossici")
            drug_diuretic = st.checkbox("Diuretici", key="Diuretici")
        with col2:
            drug_antihyp = st.checkbox("Antipertensivi", key="Antipertensivi")
            drug_chemio = st.checkbox("Chemioterapici", key="Chemioterapici")
        with col3:
            drug_fans = st.checkbox("Fans", key="Fans")
            drug_dopa = st.checkbox("Dopamine", key="Dopamine")

        selected_drug_groups = []
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
    """Renderizza i menu a selezione multipla per l'estrazione degli eventi clinici.

    Combina le categorie di farmaci selezionate con gli eventi scelti nelle varie tabelle.
    """
    with st.container(border=True):
        st.markdown("### Eventi Clinici")
        col1, col2, col3 = st.columns(3)

        # Caricamento dataset di supporto (con caching)
        chartevents_df = open_csv("first200chartevents.csv")
        outputevents_df = open_csv("outputevents.csv")
        inputevents_df = fetch_inputevents()
        procedures_df = open_csv("first200procedures.csv")
        labevents_df = open_csv("first200labevents.csv")

        # Inizializzazione della lista completa partendo dai farmaci selezionati
        all_events_objects = list(selected_drugs)

        # Multiselect suddivisi per colonne
        with col1:
            labels_chart = st.multiselect("Chartevents", chartevents_df["label"].tolist(), key="ms_chart")
            all_events_objects.extend(extract_selected_items(chartevents_df, labels_chart, "chartevents"))

            labels_input = st.multiselect("Inputevents", inputevents_df["label"].tolist(), key="ms_input")
            all_events_objects.extend(extract_selected_items(inputevents_df, labels_input, "inputevents"))

        with col2:
            labels_output = st.multiselect("Outputevents", outputevents_df["label"].tolist(), key="ms_output")
            all_events_objects.extend(extract_selected_items(outputevents_df, labels_output, "outputevents"))

        with col3:
            labels_lab = st.multiselect("Labevents", labevents_df["label"].tolist(), key="ms_lab")
            all_events_objects.extend(extract_selected_items(labevents_df, labels_lab, "labevents"))

            labels_proc = st.multiselect("Procedures", procedures_df["label"].tolist(), key="ms_proc")
            all_events_objects.extend(extract_selected_items(procedures_df, labels_proc, "procedureevents"))

        return all_events_objects


def render_window() -> dict:
    """Renderizza gli input numerici per definire la dimensione delle finestre temporali."""
    with st.container(border=True):
        st.markdown("### Dimensioni finestre")
        col1, col2, col3 = st.columns(3)

        with col1:
            ow = st.number_input("Dimensione Observation Window", min_value=1, step=1)
        with col2:
            ww = st.number_input("Dimensione Waiting Window", min_value=0, step=1)
        with col3:
            pw = st.number_input("Dimensione Prediction Window", min_value=1, step=1)

    return {"ow": ow, "ww": ww, "pw": pw}


def check_granularity(object_events) -> dict | None:
    """Mostra i selettori di granularità e aggregazione solo se pertinenti.

    Attiva il blocco se tra gli eventi selezionati vi è almeno una tabella di tipo GROUP_TABLE.
    """
    if not any(event.get("tabella") in GROUP_TABLE for event in object_events):
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


def render_ordering_section(events_objects: list, granularity_info: dict | None, windows_info: dict):
    """Gestisce il riordino interattivo delle feature tramite un multiselect sincronizzato.

    Mantiene lo stato tra i rerun di Streamlit e salva la struttura finale completa
    in `st.session_state['pipeline_input']`.
    """
    item_lookup_map = {item["parametro"]: item for item in events_objects}
    current_keys = list(item_lookup_map.keys())

    # Se nessuna feature è selezionata, resetta lo stato della pipeline
    if not current_keys:
        st.session_state["pipeline_input"] = []
        st.session_state["feature_sorter"] = []
        st.session_state["prev_current_keys"] = []
        return

    # Sincronizzazione dinamica dello stato per preservare l'ordine scelto durante le aggiunte/rimozioni
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
        st.info("Rimuovi le voci con la 'x' e reinseriscile una ad una nell'ordine desiderato.")

        ordered_labels = st.multiselect(
            "Seleziona o reinserisci nell'ordine desiderato:",
            options=current_keys,
            key="feature_sorter"
        )

        # Costruzione della lista finale di feature arricchita con le impostazioni di granularità
        final_ordered_features = []
        for label in ordered_labels:
            feature_data = item_lookup_map[label].copy()

            if granularity_info and item_lookup_map[label]["tabella"] in GROUP_TABLE:
                feature_data["granularita"] = granularity_info["granularita"]
                feature_data["aggregazione"] = granularity_info["aggregazione"]
            final_ordered_features.append(feature_data)

        # Salvataggio dell'oggetto JSON finale da inviare al backend
        st.session_state["pipeline_input"] = {
            "windows": windows_info,
            "features": final_ordered_features
        }

        # Feedback visivo dell'ordine selezionato
        if ordered_labels:
            st.markdown("**Ordine finale per l'addestramento:**")
            st.caption(" → ".join([f"`{label}`" for label in ordered_labels]))


def render_button():
    """Renderizza il pulsante di sottomissione e convalida il numero di parametri prima di procedere."""
    st.write("")
    _, col_c, _ = st.columns([1, 1, 1])

    with col_c:
        if st.button("Elabora Modello", width='stretch', type="primary"):
            pipeline_data = st.session_state.get("pipeline_input", [])

            # Controllo di validità sul numero totale di parametri selezionati (3-6)
            if not pipeline_data or (len(pipeline_data["features"]) < 3 or len(pipeline_data["features"]) > 6):
                st.warning("Seleziona dai 3 ai 6 parametri")
                return

            # Navigazione verso la pagina dei risultati
            st.switch_page("pages/result.py")


# --- FLUSSO PRINCIPALE DI ESECUZIONE ---
# Caricamento del file CSS
local_css("frontend/style/style.css")

st.title("🩺 Prediction of Kidney Injury")

# Esecuzione modulare della UI e passaggio dei dati
selected_drugs = render_farmaci()
events_objects = render_multiselect(selected_drugs)

windows = render_window()
granularity_info = check_granularity(events_objects)

# Assemblaggio dello stato globale e gestione dell'invio
render_ordering_section(events_objects, granularity_info, windows)
render_button()