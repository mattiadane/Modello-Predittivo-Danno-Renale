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



print(st.session_state["pipeline_input"])


'''
try:
    response = requests.get("http://127.0.0.1:8000/AKI",json=st.session_state["pipeline_input"])
    if response.status_code == 200:
        st.success("Dati inviati ed elaborati con successo!")
        risultati = response.json()
        df = pd.DataFrame(risultati)
        st.dataframe(df)
    else:
        st.error(f"Errore dal server ({response.status_code}): {response.text}")

except requests.exceptions.RequestException as e:
        st.error(f"Impossibile connettersi al backend: {e}")

'''

if st.button("Back to Home Page"):
    st.session_state.clear()
    st.switch_page("pages/home.py")