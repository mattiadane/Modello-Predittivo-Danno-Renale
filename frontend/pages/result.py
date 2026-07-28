import pandas as pd
import streamlit as st
import requests

st.title("Result of query")

# Verifica se esiste l'input della pipeline e se non è una lista vuota
if "pipeline_input" not in st.session_state or not st.session_state["pipeline_input"]:
    st.warning("⚠️ Nessuna configurazione trovata! Torna alla Home per selezionare le feature.")
    if st.button("⬅️ Back to Home Page"):
        st.switch_page("app.py")  # Modifica con il nome corretto della tua home page se diverso
    st.stop()  # Ferma l'esecuzione dello script qui

# Recupera la lista di dizionari completa e ordinata
pipeline_input = st.session_state["pipeline_input"]

print(pipeline_input)


try:
    response = requests.get("http://127.0.0.1:8000/patient")
    response.raise_for_status()
    data = response.json()

    # Se il JSON è una lista di oggetti → perfetto per DataFrame
    df = pd.DataFrame(data)

    st.success("Dati caricati!")
    st.dataframe(df)

except Exception as e:
    st.error(f"Errore: {e}")



if st.button("Back to Home Page"):
    st.session_state.clear()
    st.switch_page("pages/home.py")