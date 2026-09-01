import uuid

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Result of query", layout="wide")

st.title("Result of query")

# Configuration
PAGE_SIZE = 50

# 1. Inizializzazione Session State
if "tutti_i_dati" not in st.session_state:
    st.session_state["tutti_i_dati"] = None
if "pagina_corrente" not in st.session_state:
    st.session_state["pagina_corrente"] = 1
if "query_id" not in st.session_state:
    st.session_state["query_id"] = str(uuid.uuid4()) #generazione id_query casuale



query_id = st.session_state["query_id"]

def carica_tutti_i_dati():
    """Scarica l'intero dataset in un'unica chiamata."""
    try:
        payload = {"parametri": st.session_state.get("pipeline_input")}


        # Nessun parametro 'limit' o 'offset' inviato al backend
        with st.spinner("Caricamento completo dei dati in corso..."):
            response = requests.post(
                f"http://127.0.0.1:8000/AKI/{query_id}", json=payload
            )

        if response.status_code == 200:
            dati = response.json()
            if dati:
                st.session_state["tutti_i_dati"] = dati
                st.session_state["pagina_corrente"] = 1
            else:
                st.info("Non sono stati trovati pazienti che soddisfano i parametri selezionati.")
                st.session_state["tutti_i_dati"] = []
        else:
            st.error(f"Errore dal server ({response.status_code}): {response.text}")

    except requests.exceptions.RequestException as e:
        st.error(f"Richiesta interotta",{e})


# 2. Caricamento iniziale (eseguito solo la prima volta)
if st.session_state["tutti_i_dati"] is None:

    if st.button("Annulla la query e torna alla home"):
        try:
            response = requests.post(
                f"http://127.0.0.1:8000/cancel-query/{query_id}"
            )
        except Exception as e:
            st.error(e)

        st.session_state.clear()
        st.switch_page("pages/home.py")


    carica_tutti_i_dati()

# 3. Visualizzazione e Paginazione In-Memory
if st.session_state["tutti_i_dati"]:
    st.success("Dati caricati con successo!")

    tutti_i_dati = st.session_state["tutti_i_dati"]
    totale_righe = len(tutti_i_dati)
    totale_pagine = max(1, (totale_righe + PAGE_SIZE - 1) // PAGE_SIZE)

    # Assicuriamoci che la pagina corrente rientri nei limiti validi
    pagina = st.session_state["pagina_corrente"]

    # Calcolo dell'intervallo (Slice) per la pagina corrente
    start_idx = (pagina - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE

    # Estraiamo SOLO i record della pagina attuale per il DataFrame
    dati_pagina = tutti_i_dati[start_idx:end_idx]
    df_pagina = pd.DataFrame(dati_pagina)

    num_colonne = len(df_pagina.columns)
    html_table = df_pagina.to_html(classes="fixed-table", index=False)

    # Styling CSS con Scroll Orizzontale Abilitato e Min-Width
    st.markdown(
        f"""
        <style>
        .table-container {{
            max-height: 500px;
            overflow-y: auto;
            overflow-x: auto; /* Permette lo scorrimento orizzontale */
            border: 1px solid rgba(250, 250, 250, 0.2);
            border-radius: 6px;
            margin-bottom: 10px;
        }}

        .fixed-table {{
            width: 100% !important;
            min-width: {num_colonne * 140}px; /* Garantisce ampiezza sufficiente per tutte le colonne */
            table-layout: auto !important;
            border-collapse: collapse;
            font-size: 13px;
        }}

        .fixed-table th, .fixed-table td {{
            min-width: 120px; /* Evita che il testo dell'intestazione venga tagliato */
            word-wrap: break-word !important;
            white-space: normal !important;
            overflow-wrap: break-word !important;
            padding: 8px 6px;
            text-align: left;
            border: 1px solid rgba(250, 250, 250, 0.1);
        }}

        .fixed-table th {{
            position: sticky;
            top: 0;
            background-color: #1e1e1e;
            z-index: 2;
            font-weight: bold;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Render HTML
    st.markdown(
        f'<div class="table-container">{html_table}</div>',
        unsafe_allow_html=True,
    )

    # Caption informativa
    st.caption(
        f"Mostrati record {start_idx + 1} - {min(end_idx, totale_righe)} di {totale_righe} | "
        f"Pagina {pagina} di {totale_pagine}"
    )

    # Controlli di navigazione (Precedente / Pagina / Successiva)
    col_prev, col_page, col_next, _ = st.columns([1, 2, 1, 3])

    with col_prev:
        if st.button("⬅️ Precedente", disabled=(pagina == 1)):
            st.session_state["pagina_corrente"] -= 1
            st.rerun()

    with col_page:
        nuova_pagina = st.number_input(
            "Pagina",
            min_value=1,
            max_value=totale_pagine,
            value=pagina,
            label_visibility="collapsed",
        )
        if nuova_pagina != pagina:
            st.session_state["pagina_corrente"] = nuova_pagina
            st.rerun()

    with col_next:
        if st.button("Successiva ➡️", disabled=(pagina == totale_pagine)):
            st.session_state["pagina_corrente"] += 1
            st.rerun()

# Pulsante di ritorno
if st.button("Back to Home Page"):
    st.session_state.clear()
    st.switch_page("pages/home.py")