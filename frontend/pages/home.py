import os
import pandas as pd
import streamlit as st
from database.connection import Connection


class HomePage:

    def __init__(self):
        # Path base del progetto
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
                "nephro": False,
                "sepsi": False,
                "diuretic": False,
                "venpres": None,
                "conmed": False,
                "surgical_op": False,
                "sispress": None,
                "antihypertensive": False,
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
                st.session_state.state["nephro"] = st.checkbox("Nephrotoxicity drugs")
            with col2:
                st.session_state.state["diuretic"] = st.checkbox("Diuretic drugs")
            with col3:
                st.session_state.state["antihypertensive"] = st.checkbox("Antihypertensive drugs")

    def render_pressioni(self):
        with st.container(border=True):
            st.markdown("### Pressioni")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.state["venpres"] = st.checkbox("Enable venous pressure") or None
            with col3:
                st.session_state.state["sispress"] = st.checkbox("Enable systolic pressure") or None

    def render_condizioni(self):
        with st.container(border=True):
            st.markdown("### Condizioni")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.state["sepsi"] = st.checkbox("Sepsi")
            with col2:
                st.session_state.state["conmed"] = st.checkbox("Contrast Medium")
            with col3:
                st.session_state.state["surgical_op"] = st.checkbox("Surgical Operation")

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

                df = self.con.query("SELECT * FROM patients LIMIT 10")
                if df is not None and not df.empty:
                    st.session_state.state["example"] = df
                st.switch_page("pages/result.py")


    def render(self):
        st.title("Prediction of Kidney Injury")
        self.render_farmaci()
        self.render_pressioni()
        self.render_condizioni()
        self.render_multiselect()
        self.render_button()


HomePage().render()