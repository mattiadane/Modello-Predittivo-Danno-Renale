import streamlit as st

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
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Richiama la funzione passando il nome del file
local_css("front-end/style/style.css")

st.set_page_config(page_title="Kidney Injury", page_icon="🧬")



st.title("Prediction of Kidney Injury")


check_nephro = st.checkbox("Nephrotoxicity drugs")
if check_nephro:
    st.session_state.state["nephro"] = True


check_sepsi = st.checkbox("Sepsi")
if check_sepsi:
    st.session_state.state["sepsi"] = True


check_diuretic = st.checkbox("Diuretic drugs")
if check_diuretic:
    st.session_state.state["diuretic"] = True


check_conmed = st.checkbox("Contrast Medium")
if check_conmed:
    st.session_state.state["conmed"] = True



enable_slider1 = st.checkbox("Enable parameter venouse pressoure")

if enable_slider1:
    st.session_state.state["venpres"] =  st.slider("Select min value ",-10,20)
else:
    st.session_state.state["venpres"] = None


check_surgical_op = st.checkbox("surgical operation")
if check_surgical_op:
    st.session_state.state["surgical_op"] = True



enable_slider2 = st.checkbox("Enable parameter sistolic pressoure")

if enable_slider2 :
    st.session_state.state["sispress"] =  st.slider("Select min value ",50,160)
else:
    st.session_state.state["sispress"] = None

check_antihypertensive = st.checkbox("Antihypertensive drugs")
if check_antihypertensive:
    st.session_state.state["antihypertensive"] = True


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
