import streamlit as st
from database.connection import Connection
from frontend.vocabolario import *

@st.cache_resource
def get_database_connection():
    return Connection()

con = get_database_connection()



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
        "example" : None
    }

def local_css(file_name):
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown("<style>" + f.read() + "</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass
local_css("frontend/style/style.css")

st.title("Prediction of Kidney Injury")

# ===== FARMACI — 3 colonne =====
with st.container(border=True):
    st.markdown("### Farmaci")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.state["nephro"] = st.checkbox("Nephrotoxicity drugs")
    with col2:
        st.session_state.state["diuretic"] = st.checkbox("Diuretic drugs")
    with col3:
        st.session_state.state["antihypertensive"] = st.checkbox("Antihypertensive drugs")

# ===== PRESSIONI — 3 colonne =====
with st.container(border=True):
    st.markdown("### Pressioni")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("Enable venous pressure"):
            st.session_state.state["venpres"] = True
        else:
            st.session_state.state["venpres"] = None
    with col3:
        if st.checkbox("Enable systolic pressure"):
            st.session_state.state["sispress"] = True
        else:
            st.session_state.state["sispress"] = None

# ===== ALTRI FLAGS — 3 colonne =====
with st.container(border=True):
    st.markdown("### Condizioni")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("Sepsi"):
            st.session_state.state["sepsi"] = True
        else:
            st.session_state.state["sepsi"] = False
    with col2:
        if st.checkbox("Contrast Medium"):
            st.session_state.state["conmed"] = True
        else:
            st.session_state.state["conmed"] = False
    with col3:
        if st.checkbox("Surgical Operation"):
            st.session_state.state["surgical_op"] = True
        else:
            st.session_state.state["surgical_op"] = False

# ===== MULTISELECT =====
scelta = st.multiselect("Scegli un termine:", CHARTEVENTS)

# ===== BOTTONE CENTRATO =====
st.write("")
col_l, col_c, col_r = st.columns([1, 1, 1])
with col_c:
    button_opendialog = st.button("Choose Framework", use_container_width=True)
    if button_opendialog:
        df = con.query("SELECT * FROM patients LIMIT 10")
        if df is not None and not df.empty:
            st.session_state.state["example"] = df
        st.switch_page("pages/result.py")