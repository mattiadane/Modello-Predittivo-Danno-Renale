import streamlit as st

if "state" not in st.session_state:
    st.session_state.state = {
        "surgical_op": False
    }

# funzione per aprire il file css
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Richiama la funzione passando il nome del file
local_css("front-end/style/style.css")

st.set_page_config(page_title="Kidney Injury", page_icon="🧬")



st.title("Prediction of Kidney Injury")


button_nephro = st.button("Nephrotoxicity drugs")



if button_nephro:
    st.write("Nephrotoxicity drugs")
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
    st.session_state.state["surgical_op"] = True


min_sis_pres= st.slider("Select min value ",50,160)
st.write("hai selezionato il valore ", min_sis_pres)


button_antihypertensive = st.button("Antihypertensive drugs")
if button_antihypertensive:
    st.write("Antihypertensive drugs")
    # richiamare query per selezionare farmaci antiipertensività



button_opendialog = st.button("Choose Framework")


@st.dialog("Select framework")
def select_framework():
    messaa = " Hai selezionato surgical op?"
    if st.session_state.state["surgical_op"]:
        messaa += " Si"
    else :
        messaa += " No"

    st.write(messaa)

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
