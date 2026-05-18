import streamlit as st

st.set_page_config(page_title="Kidney Injury", page_icon="🧬")

# Definiamo le pagine puntando ai file corretti
# Spostiamo la logica della home dentro la cartella views
home_page = st.Page("views/home.py", title="Home", icon="🧬", default=True)
result_page = st.Page("pages/result.py", title="Result")

# Creiamo la navigazione NASCOSTA
pg = st.navigation([home_page, result_page], position="hidden")

# Avviamo l'applicazione
pg.run()