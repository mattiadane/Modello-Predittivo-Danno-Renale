import os
import pandas as pd
import streamlit as st
from database.connection import Connection


class HomePage:

    def __init__(self):
        self.PRESSURE_ITEMIDS = {
            220179: "Non Invasive Blood Pressure systolic",
            220050: "Arterial Blood Pressure systolic",
            220074: "Central Venous Pressure",
        }

        self.GRANULARITY_OPTIONS = {
            "15 minuti": "15min",
            "30 minuti": "30min",
            "1 ora": "1h",
            "4 ore": "4h",
            "1 giorno": "1d",
        }

        self.AGGREGATION_OPTIONS = ["Media", "Minimo", "Massimo"]

        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")

        self.con = self.get_database_connection()

        # Inizializzazione dello Stato Globale
        if "state" not in st.session_state:
            st.session_state.state = {
                "example": None,
                "selected_features": {
                    "chartevents": [], "inputevents": [], "outputevents": [],
                    "labevents": [], "procedures": []
                },
                "selected_drugs": [],  # Salva i farmaci selezionati
                "selected_labels": [],  # Unione di farmaci + eventi clinici
                "ordered_features_labels": [],  # Ordine finale totale
                "granularity_state": {"gran_label": "1 ora", "agg_label": "Media"}
            }

        self.local_css("frontend/style/style.css")

    @st.cache_data
    def open_csv(_self, filename):
        path = os.path.join(_self.DATA_DIR, filename)
        if os.path.exists(path):
            return pd.read_csv(path).dropna(how="all")
        return pd.DataFrame(columns=["itemid", "label"])

    @st.cache_resource
    def get_database_connection(_self):
        return Connection()

    def local_css(self, file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown("<style>" + f.read() + "</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            pass

    def render_farmaci(self):
        with st.container(border=True):
            st.markdown("### Farmaci")
            col1, col2, col3 = st.columns(3)

            # Assegniamo chiavi univoche per intercettare i valori
            with col1:
                drug_nephro = st.checkbox("Nephrotoxicity drugs", key="drug_nephro")
            with col2:
                drug_diuretic = st.checkbox("Diuretic drugs", key="drug_diuretic")
            with col3:
                drug_antihyp = st.checkbox("Antihypertensive drugs", key="drug_antihyp")

            # Popoliamo la lista dei farmaci selezionati nello stato
            selected_drugs = []
            if drug_nephro: selected_drugs.append("Nephrotoxicity drugs")
            if drug_diuretic: selected_drugs.append("Diuretic drugs")
            if drug_antihyp: selected_drugs.append("Antihypertensive drugs")

            st.session_state.state["selected_drugs"] = selected_drugs

    def render_multiselect(self):
        with st.container(border=True):
            st.markdown("### Eventi Clinici")
            col1, col2, col3 = st.columns(3)

            chartevents_df = self.open_csv("first200chartevents.csv")
            outputevents_df = self.open_csv("outputevents.csv")
            inputevents_df = self.open_csv("first200inputevents.csv")
            procedures_df = self.open_csv("first200procedures.csv")
            labevents_df = self.open_csv("first200labevents.csv")

            # Partiamo inserendo nell'aggregatore le label dei farmaci scelti sopra
            current_labels = list(st.session_state.state["selected_drugs"])

            with col1:
                labels_chart = st.multiselect("Chartevents", chartevents_df["label"].tolist(), key="ms_chart")
                st.session_state.state["selected_features"]["chartevents"] = \
                chartevents_df[chartevents_df["label"].isin(labels_chart)]["itemid"].tolist()
                current_labels.extend(labels_chart)

                labels_input = st.multiselect("Inputevents", inputevents_df["label"].tolist(), key="ms_input")
                st.session_state.state["selected_features"]["inputevents"] = \
                inputevents_df[inputevents_df["label"].isin(labels_input)]["itemid"].tolist()
                current_labels.extend(labels_input)

            with col2:
                labels_output = st.multiselect("Outputevents", outputevents_df["label"].tolist(), key="ms_output")
                st.session_state.state["selected_features"]["outputevents"] = \
                outputevents_df[outputevents_df["label"].isin(labels_output)]["itemid"].tolist()
                current_labels.extend(labels_output)

            with col3:
                labels_lab = st.multiselect("Labevents", labevents_df["label"].tolist(), key="ms_lab")
                st.session_state.state["selected_features"]["labevents"] = \
                labevents_df[labevents_df["label"].isin(labels_lab)]["itemid"].tolist()
                current_labels.extend(labels_lab)

                labels_proc = st.multiselect("Procedures", procedures_df["label"].tolist(), key="ms_proc")
                st.session_state.state["selected_features"]["procedures"] = \
                procedures_df[procedures_df["label"].isin(labels_proc)]["itemid"].tolist()
                current_labels.extend(labels_proc)

            # Salviamo l'unione totale (Farmaci + Eventi) nello stato
            st.session_state.state["selected_labels"] = current_labels

            self.check_granularity()

    def check_granularity(self):
        chartevents_ids = st.session_state.state["selected_features"]["chartevents"]
        is_pressure = any(id_chart in self.PRESSURE_ITEMIDS for id_chart in chartevents_ids)

        if not is_pressure:
            return

        st.write("---")
        st.write("**Configurazione Pressione:**")
        col_g, col_a = st.columns(2)
        with col_g:
            gran_label = st.selectbox("Granularità", options=list(self.GRANULARITY_OPTIONS.keys()), index=2,
                                      key="sb_gran")
        with col_a:
            agg_label = st.selectbox("Aggregazione", options=self.AGGREGATION_OPTIONS, index=0, key="sb_agg")

        st.session_state.state["granularity_state"]["gran_label"] = gran_label
        st.session_state.state["granularity_state"]["agg_label"] = agg_label

    def render_ordering_section(self):
        """Mostra una sezione per ordinare tutte le feature (farmaci + eventi)."""
        selected_labels = st.session_state.state["selected_labels"]

        if not selected_labels:
            return

        with st.container(border=True):
            st.markdown("### Ordina le tue Feature (Farmaci ed Eventi)")
            st.info("Rimuovi e riaggiungi le voci per decidere l'ordine con cui alimentare il modello.")

            ordered_labels = st.multiselect(
                "Trascina o seleziona nell'ordine desiderato:",
                options=selected_labels,
                default=selected_labels,
                key="feature_sorter"
            )

            st.session_state.state["ordered_features_labels"] = ordered_labels

            if ordered_labels:
                st.markdown("**Ordine finale per l'addestramento:**")
                st.caption(" → ".join([f"`{label}`" for label in ordered_labels]))

    def render_button(self):
        st.write("")
        _, col_c, _ = st.columns([1, 1, 1])

        with col_c:
            if st.button("Elabora Modello", use_container_width=True, type="primary"):
                final_order = st.session_state.state["ordered_features_labels"]

                print("ORDINE COMPLETO (FARMACO + EVENTI):", final_order)

                print(st.session_state.state["selected_features"])

                try:
                    df = self.con.query("SELECT * FROM patients LIMIT 10")
                    if df is not None and not df.empty:
                        st.session_state.state["example"] = df
                except Exception as e:
                    st.error(f"Errore DB: {e}")
                    return

                st.switch_page("pages/result.py")

    def render(self):
        st.title("🩺 Prediction of Kidney Injury")
        self.render_farmaci()  # 1. Carica i farmaci e li salva nello stato
        self.render_multiselect()  # 2. Unisce i farmaci agli eventi clinici selezionati
        self.render_ordering_section()  # 3. Permette il riordinamento totale
        self.render_button()


HomePage().render()