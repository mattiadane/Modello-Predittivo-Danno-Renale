import pandas as pd
import streamlit as st
import requests

st.title("Result of query")

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