import select
import streamlit as st

if "nephro" not in st.session_state:
    st.session_state.nephro = []

# funzione per aprire il file css
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Richiama la funzione passando il nome del file
local_css("front-end/style/style.css")


st.title("Predizione Danno Renale")


button_nephro = st.button("Nephrotoxicity drugs")



if button_nephro:
    st.write("Nephrotoxicity drugs")
    st.session_state.nephro.append("Gentamicin")
    # richiamare query per selezionare farmaci nefrotossici

button_sepsi = st.button("Sepsi")
if button_sepsi:
    st.write("Sepsi")
    # richiamare query per selezionare sepsi


button_diuretic = st.button("Diuretic drugs")
if button_diuretic:
    st.write("Diuretic drugs")
    # richiamare query per selezionare farmaci direttici


min_central_ven_pres= st.slider("Select min value ",-10,20)
st.write("hai selezionato il valore ", min_central_ven_pres)

button_conmed = st.button("Contrast Medium")
if button_conmed:
    st.write("Contrast Medium")
    # richiamare query per selezionare constrasto medio


check_surgical_op = st.checkbox("surgical operation")
if check_surgical_op:
    st.write("Surgical operation is clicked")
    # richiamare query per selezionare operazioni


min_sis_pres= st.slider("Select min value ",50,160)
st.write("hai selezionato il valore ", min_sis_pres)


button_antihypertensive = st.button("Antihypertensive drugs")
if button_antihypertensive:
    st.write("Antihypertensive drugs")
    # richiamare query per selezionare farmaci antiipertensività



button_opendialog = st.button("Choose Framework")


@st.dialog("Select framework")
def select_framework():

    choice = st.radio(
        "Seleziona un'framework:",
        ["framework 1", "Framework 2"],
        horizontal=True  # Per metterle affiancate come checkbox
    )
    button_submit = st.button("Submit")

    if button_submit:

        st.write("hai selezionato " + choice)
        st.write(st.session_state.nephro[0])



if button_opendialog:
    select_framework()
