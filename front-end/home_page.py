import streamlit as st

st.set_page_config(page_title="Kidney Injury", page_icon="🧬")

if "state" not in st.session_state:
    st.session_state.state = {
        "nephro" : False,
        "spesi": False,
        "diuretic" : False,
        "venpres" : None,
        "conmed": False,
        "surgical_op": False,
        "sispress" : None,
        "antihypertensive" : False,
    }

# funzione per aprire il file css
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Richiama la funzione passando il nome del file
local_css("front-end/style/style.css")

st.title("Prediction of Kidney Injury")

# ===== FARMACI =====
with st.container(border=True):
    st.markdown("### Farmaci")
    st.session_state.state["nephro"] = st.checkbox("Nephrotoxicity drugs")
    st.session_state.state["diuretic"] = st.checkbox("Diuretic drugs")
    st.session_state.state["antihypertensive"] = st.checkbox("Antihypertensive drugs")

# ===== PRESSIONI =====
with st.container(border=True):
    st.markdown("### Pressioni")

    if st.checkbox("Enable venous pressure"):
        st.session_state.state["venpres"] = st.slider("Venous pressure", -10, 20)
    else:
        st.session_state.state["venpres"] = None

    if st.checkbox("Enable systolic pressure"):
        st.session_state.state["sispress"] = st.slider("Systolic pressure", 50, 160)
    else:
        st.session_state.state["sispress"] = None

st.write("")

check_sepsi = st.checkbox("Sepsi")
if check_sepsi:
    st.session_state.state["sepsi"] = True

st.write("")

check_conmed = st.checkbox("Contrast Medium")
if check_conmed:
    st.session_state.state["conmed"] = True

st.write("")

check_surgical_op = st.checkbox("Surgical Operation")
if check_surgical_op:
    st.session_state.state["surgical_op"] = True

button_opendialog = st.button("Choose Framework")

@st.dialog("Select framework")
def select_framework():

    st.write("hai selezionato  : ", st.session_state.state)
    choice = st.radio(
        "Seleziona un'framework:",
        ["framework 1", "Framework 2"],
        horizontal=True  # Per metterle affiancate come checkbox
    )
    button_submit = st.button("Submit")

    if button_submit:
        st.write("hai selezionato " + choice )

if button_opendialog:
    select_framework()
