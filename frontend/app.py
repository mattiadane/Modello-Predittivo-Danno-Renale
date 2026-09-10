import streamlit as st

# --- Configurazione Iniziale ---
# Imposta il titolo della scheda del browser e l'icona dell'applicazione.
st.set_page_config(page_title="Kidney Injury", page_icon="🧬")

# --- Definizione dell'Albero di Navigazione ---
# Mappa i singoli file Python come pagine dell'applicazione usando st.Page.
# - default=True fissa la pagina iniziale al caricamento dell'app.
# - L'uso di "pages/" permette di modularizzare la struttura delle viste.
home_page = st.Page("pages/home.py", title="Home", icon="🧬", default=True)
result_page = st.Page("pages/result.py", title="Result")

# --- Configurazione del Controller di Navigazione ---
# Registra le pagine definite. Il parametro position="hidden" rimuove
# la sidebar di navigazione nativa di Streamlit, utile per gestire
# programmaticamente i reindirizzamenti (es. tramite st.switch_page).
pg = st.navigation([home_page, result_page], position="hidden")

# --- Esecuzione ---
# Esegue il rendering della pagina correntemente attiva nello stack di navigazione.
pg.run()