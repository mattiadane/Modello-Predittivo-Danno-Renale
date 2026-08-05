import os
import pandas as pd
import streamlit as st

# --- COSTANTI E PERCORSI ---

NEPRO = [
    "Gentamicin", "Vancomycin", "Tobramycin", "Amikacin", "Penicillamine",
    "Auranofin", "Sulfamethoxazole", "Trimethoprim", "Sulfametrole",
    "Sulfamazone", "Streptomycin", "Netilmicin", "Zoledronate", "Colistin",
    "Acyclovir", "Foscavir", "Ganciclovir", "Adefovir", "Tenofovir",
    "Indinavir", "Cidofovir", "Cyclosporine", "Tacrolimus", "Carmustine",
    "Mutamycin", "Prevacid", "Pamidronate"
]

DIUR = [
    "Furosemide", "Triamterene", "Hydrochlorothiazide", "Indapamide",
    "Spironolactone", "Tolvaptan", "Chlorothiazide", "Bumetanide",
    "Amiloride", "Metolazone", "Eplerenone", "Chlorthalidone",
    "Torsemide", "Aldactone", "Ethacrynic acid", "Acetazolamide"
]

ANTIPER = [
    "Nebivolol", "Moexipril", "Sotalol", "Lisinopril", "Carvedilol",
    "Methyldopa", "Propranolol", "Benazepril", "Aliskiren", "Ambrisentan",
    "Clonidine", "Pindolol", "Bosentan", "Minoxidil", "Irbesartan",
    "Prazosin", "Quinapril", "Doxazosin", "Atenolol", "Diazoxide",
    "Metoprolol", "Esmolol", "Candesartan", "Nadolol", "Losartan",
    "Captopril", "Valsartan", "Trandolapril", "Acebutolol", "Ramipril",
    "Macitentan", "Guanfacine"
]

DRUG_GROUPS_MAP = {
    "Nephrotoxicity drugs": NEPRO,
    "Diuretic drugs": DIUR,
    "Antihypertensive drugs": ANTIPER
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

VITAL_ITEMIDS = {
    220180: "Non Invasive Blood Pressure diastolic",
    220181: "Non Invasive Blood Pressure mean",
    220179: "Non Invasive Blood Pressure systolic",
    220050: "Arterial Blood Pressure systolic",
    220051: "Arterial Blood Pressure diastolic",
    220052: "Arterial Blood Pressure mean",
    220074: "Central Venous Pressure",
    220045: "Heart Rate",
    220210: "Respiratory Rate",
    220277: "SpO2"
}

GRANULARITY_OPTIONS = {
    "1 ora": "1h",
    "3 ore": "3h",
    "6 ore": "6h",
}

AGGREGATION_OPTIONS = ["Media", "Minimo", "Massimo"]


# --- HELPER PER CARICAMENTO DATI ---
@st.cache_data
def open_csv(filename: str) -> pd.DataFrame:
    """Carica un file CSV dalla cartella data se esiste."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path).dropna(how="all")
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
            "parametro": str(row["label"])
        }
        for _, row in filtered_df.iterrows()
    ]


# --- SEZIONI UI ---
def render_farmaci() -> list:
    """Renderizza la selezione farmaci e restituisce in locale le macrocategorie scelte."""
    with st.container(border=True):
        st.markdown("### Farmaci")
        col1, col2, col3 = st.columns(3)

        with col1:
            drug_nephro = st.checkbox("Nephrotoxicity drugs", key="drug_nephro")
        with col2:
            drug_diuretic = st.checkbox("Diuretic drugs", key="drug_diuretic")
        with col3:
            drug_antihyp = st.checkbox("Antihypertensive drugs", key="drug_antihyp")

        selected_drug_groups = []
        if drug_nephro:
            selected_drug_groups.append("Nephrotoxicity drugs")
        if drug_diuretic:
            selected_drug_groups.append("Diuretic drugs")
        if drug_antihyp:
            selected_drug_groups.append("Antihypertensive drugs")

        return selected_drug_groups


def render_multiselect(selected_drugs: list) -> tuple[list, list]:
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
        inputevents_df = open_csv("first200inputevents.csv")
        procedures_df = open_csv("first200procedures.csv")
        labevents_df = open_csv("first200labevents.csv")

        current_labels = list(selected_drugs)
        all_events_objects = []

        with col1:
            labels_chart = st.multiselect("Chartevents", chartevents_df["label"].tolist(), key="ms_chart")
            all_events_objects.extend(extract_selected_items(chartevents_df, labels_chart, "chartevents"))
            current_labels.extend(labels_chart)

            labels_input = st.multiselect("Inputevents", inputevents_df["label"].tolist(), key="ms_input")
            all_events_objects.extend(extract_selected_items(inputevents_df, labels_input, "inputevents"))
            current_labels.extend(labels_input)

        with col2:
            labels_output = st.multiselect("Outputevents", outputevents_df["label"].tolist(), key="ms_output")
            all_events_objects.extend(extract_selected_items(outputevents_df, labels_output, "outputevents"))
            current_labels.extend(labels_output)

        with col3:
            labels_lab = st.multiselect("Labevents", labevents_df["label"].tolist(), key="ms_lab")
            all_events_objects.extend(extract_selected_items(labevents_df, labels_lab, "labevents"))
            current_labels.extend(labels_lab)

            labels_proc = st.multiselect("Procedures", procedures_df["label"].tolist(), key="ms_proc")
            all_events_objects.extend(extract_selected_items(procedures_df, labels_proc, "procedureevents"))
            current_labels.extend(labels_proc)

        # Rimuove duplicati mantenendo l'ordine
        available_labels = list(dict.fromkeys(current_labels))
        return available_labels, all_events_objects


def check_granularity(events_objects: list) -> dict | None:
    """Mostra la configurazione di granularità solo se è presente un parametro vitale in Chartevents."""
    chart_ids = [item["id"] for item in events_objects if item["tabella"] == "chartevents"]
    is_pressure = any(id_chart in VITAL_ITEMIDS for id_chart in chart_ids)

    if not is_pressure:
        return None

    st.write("---")
    st.write("**Configurazione Parametri vitali:**")
    col_g, col_a = st.columns(2)

    with col_g:
        gran_label = st.selectbox(
            "Granularità",
            options=list(GRANULARITY_OPTIONS.keys()),
            index=2,
            key="sb_gran"
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


def render_ordering_section(available_options: list, events_objects: list, granularity_info: dict | None):
    """
    Costruisce l'interfaccia di riordino e salva DIRETTAMENTE in st.session_state['pipeline_input']
    l'unico array finale completo di cui hai bisogno.
    """
    if not available_options:
        st.session_state["pipeline_input"] = []
        if "feature_sorter" in st.session_state:
            st.session_state.feature_sorter = []
        return

    # Sincronizzazione locale del widget multiselect
    if "feature_sorter" not in st.session_state:
        st.session_state.feature_sorter = available_options.copy()
    else:
        st.session_state.feature_sorter = [
            item for item in st.session_state.feature_sorter if item in available_options
        ]

    with st.container(border=True):
        st.markdown("### Ordina le tue Feature (Macro-Farmaci ed Eventi)")
        st.info("Rimuovi le voci con la 'x' e rinseriscile una ad una nell'ordine desiderato.")

        ordered_labels = st.multiselect(
            "Seleziona o reinserisci nell'ordine desiderato:",
            options=available_options,
            key="feature_sorter"
        )

        # Mappa veloce locale: Nome Parametro -> Oggetto Evento
        item_lookup_map = {item["parametro"]: item for item in events_objects}

        # Costruzione dell'UNICO array che servirà al backend
        final_ordered_features = []
        for label in ordered_labels:
            # Caso Farmaco
            if label in DRUG_GROUPS_MAP:
                final_ordered_features.append({
                    "tabella": "farmaci",
                    "parametro": label,
                    "items": DRUG_GROUPS_MAP[label]
                })
            # Caso Evento Clinico
            elif label in item_lookup_map:
                event_data = item_lookup_map[label].copy()

                # Inserisce granularità/aggregazione se è una pressione
                if event_data["id"] in VITAL_ITEMIDS and granularity_info:
                    event_data["granularita"] = granularity_info["granularita"]
                    event_data["aggregazione"] = granularity_info["aggregazione"]

                final_ordered_features.append(event_data)

        # SALVIAMO UNICAMENTE L'ARRAY FINALE PER IL BACKEND
        st.session_state["pipeline_input"] = final_ordered_features

        if ordered_labels:
            st.markdown("**Ordine finale per l'addestramento:**")
            st.caption(" → ".join([f"`{label}`" for label in ordered_labels]))


def render_button():
    """Pulsante per procedere alla pagina dei risultati."""
    st.write("")
    _, col_c, _ = st.columns([1, 1, 1])

    with col_c:
        if st.button("Elabora Modello", use_container_width=True, type="primary"):
            pipeline_data =  st.session_state.get("pipeline_input", [])

            len(pipeline_data)

            if not pipeline_data or ( len(pipeline_data) < 3  or len(pipeline_data) > 6):
                st.warning("Seleziona dai 3 ai 6 parametri")
                return

            st.switch_page("pages/result.py")


# --- FLUSSO PRINCIPALE ---
local_css("frontend/style/style.css")

st.title("🩺 Prediction of Kidney Injury")

# Passaggio dati puramente in locale tra le funzioni:
selected_drugs = render_farmaci()
available_labels, events_objects = render_multiselect(selected_drugs)
granularity_info = check_granularity(events_objects)

# Assembly finale direttamente in session_state['pipeline_input']
render_ordering_section(available_labels, events_objects, granularity_info)
render_button()