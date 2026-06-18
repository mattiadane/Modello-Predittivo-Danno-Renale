import os
import pandas as pd
import streamlit as st
from database.connection import Connection


class HomePage:

    def __init__(self):
        self.granularity_state = {}


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


        self.inputevents_ids = None
        self.procedures_ids = None
        self.outputevents_ids = None
        self.chartevents_ids = None
        self.labevents_ids = None
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")

        # Connessione DB
        self.con = self.get_database_connection()

        # Stato iniziale
        if "state" not in st.session_state:
            st.session_state.state = {
                "example": None
            }

        # Carica CSS
        self.local_css("frontend/style/style.css")

    # -----------------------------
    # UTILS
    # -----------------------------
    def open_csv(self, filename):
        """Carica CSV dal path corretto e rimuove righe vuote."""
        path = os.path.join(self.DATA_DIR, filename)
        df = pd.read_csv(path)
        return df.dropna(how="all")

    @st.cache_resource
    def get_database_connection(_self):
        return Connection()

    def local_css(self, file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown("<style>" + f.read() + "</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            pass

    # -----------------------------
    # UI COMPONENTS
    # -----------------------------
    def render_farmaci(self):
        with st.container(border=True):
            st.markdown("### Farmaci")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.checkbox("Nephrotoxicity drugs")
            with col2:
                st.checkbox("Diuretic drugs")
            with col3:
                st.checkbox("Antihypertensive drugs")

    def render_multiselect(self):
        with st.container(border=True):
            st.markdown("### Eventi Clinici")

            col1, col2, col3 = st.columns(3)

            # Caricamento CSV
            chartevents_df = self.open_csv("first200chartevents.csv")
            outputevents_df = self.open_csv("outputevents.csv")
            inputevents_df = self.open_csv("first200inputevents.csv")
            procedures_df = self.open_csv("first200procedures.csv")
            labevents_df = self.open_csv("first200labevents.csv")

            # --- COLONNA 1 ---
            with col1:
                labels = st.multiselect("Chartevents", chartevents_df["label"].tolist())
                self.chartevents_ids = chartevents_df[
                    chartevents_df["label"].isin(labels)
                ]["itemid"].tolist()

                labels = st.multiselect("Inputevents", inputevents_df["label"].tolist())
                self.inputevents_ids = inputevents_df[
                    inputevents_df["label"].isin(labels)
                ]["itemid"].tolist()

            # --- COLONNA 2 ---
            with col2:
                labels = st.multiselect("Outputevents", outputevents_df["label"].tolist())
                self.outputevents_ids = outputevents_df[
                    outputevents_df["label"].isin(labels)
                ]["itemid"].tolist()



            # --- COLONNA 3 ---
            with col3:
                labels = st.multiselect("Labevents", labevents_df["label"].tolist())
                self.labevents_ids = labevents_df[
                    labevents_df["label"].isin(labels)
                ]["itemid"].tolist()

                labels = st.multiselect("Procedures", procedures_df["label"].tolist())
                self.procedures_ids = procedures_df[
                    procedures_df["label"].isin(labels)
                ]["itemid"].tolist()

            self.check_granularity()



    def check_granularity(self):
        isPressure = False
        for id_chart in self.chartevents_ids:
            if id_chart in self.PRESSURE_ITEMIDS:
                isPressure = True

        if not isPressure:
            return

        st.write("Seleziona ogni quanto prendere le pressioni e se il minimo/massimo/media")

        col_g, col_a = st.columns(2)

        with col_g:
            gran_label = st.selectbox(
                f"Granularità",
                options=list(self.GRANULARITY_OPTIONS.keys()),
                index=2,  # default "1 ora"
                key=f"gran",
            )
        with col_a:
            agg_label = st.selectbox(
                f"Aggregazione",
                options=self.AGGREGATION_OPTIONS,
                index=0,  # default "Media"
                key=f"agg",
            )

        self.granularity_state["gran_label"] = gran_label
        self.granularity_state["agg_label"] = agg_label

    def render_button(self):
        st.write("")
        col_l, col_c, col_r = st.columns([1, 1, 1])


        with col_c:
            if st.button("Choose Framework", use_container_width=True):
                print(self.chartevents_ids)
                print(self.labevents_ids)
                print(self.inputevents_ids)
                print(self.procedures_ids)
                print(self.outputevents_ids)
                print(self.granularity_state)

                df = self.con.query("SELECT * FROM patients LIMIT 10")
                if df is not None and not df.empty:
                    st.session_state.state["example"] = df
                st.switch_page("pages/result.py")


    def render(self):
        st.title("Prediction of Kidney Injury")
        self.render_farmaci()
        self.render_multiselect()
        self.render_button()


HomePage().render()