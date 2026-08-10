import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Result of query", layout="wide")

st.title("Result of query")

if "dati_accumulatori" not in st.session_state:
    st.session_state["dati_accumulatori"] = []
if "current_offset" not in st.session_state:
    st.session_state["current_offset"] = 0
if "has_more" not in st.session_state:
    st.session_state["has_more"] = True


def carica_prossime_righe():
    try:
        payload = {"parametri": st.session_state.get("pipeline_input")}
        params = {"limit": 50, "offset": st.session_state["current_offset"]}

        response = requests.get(
            "http://127.0.0.1:8000/AKI", json=payload, params=params
        )

        if response.status_code == 200:
            nuove_righe = response.json()

            if nuove_righe:
                st.session_state["dati_accumulatori"].extend(nuove_righe)
                st.session_state["current_offset"] += len(nuove_righe)

                if len(nuove_righe) < 50:
                    st.session_state["has_more"] = False
            else:
                st.session_state["has_more"] = False
        else:
            st.error(
                f"Errore dal server ({response.status_code}): {response.text}"
            )
    except requests.exceptions.RequestException as e:
        st.error(f"Impossibile connettersi al backend: {e}")


# Primo caricamento automatico
if not st.session_state["dati_accumulatori"] and st.session_state["has_more"]:
    carica_prossime_righe()

# Visualizzazione della tabella e dei controlli
if st.session_state["dati_accumulatori"]:
    st.success("Dati caricati con successo!")

    df = pd.DataFrame(st.session_state["dati_accumulatori"])

    # 1. Calcolo dinamico delle colonne
    num_colonne = len(df.columns)

    # Assegniamo ~140px a colonna, ma non scendiamo sotto il 100% per riempire bene lo schermo
    larghezza_calcolata = f"max(100%, {num_colonne * 140}px)"

    # Genera la tabella HTML senza indice
    html_table = df.to_html(classes="fixed-table", index=False)

    # 2. Iniezione CSS avanzata
    st.markdown(
        f"""
        <style>
        /* Contenitore ad altezza e larghezza fissa con scroll verticale */
        .table-container {{
            max-height: 500px; /* Altezza fissa della tabella */
            overflow-y: auto;  /* Scroll verticale solo per scorrere i dati */
            overflow-x: hidden; /* Blocca del tutto lo scroll orizzontale */
            border: 1px solid rgba(250, 250, 250, 0.2);
            border-radius: 6px;
            margin-bottom: 10px;
        }}

        .fixed-table {{
            width: {larghezza_calcolata} !important;
            table-layout: fixed !important;
            border-collapse: collapse;
            font-size: 13px;
        }}

        .fixed-table th, .fixed-table td {{
            word-wrap: break-word !important;
            white-space: normal !important;
            overflow-wrap: break-word !important;
            padding: 8px 6px;
            text-align: left;
            border: 1px solid rgba(250, 250, 250, 0.1);
        }}

        /* Intestazione fissa in alto quando si fa lo scroll verticale */
        .fixed-table th {{
            position: sticky;
            top: 0;
            background-color: #1e1e1e; /* Sfondo scuro per bloccare le righe sotto */
            z-index: 2;
            font-weight: bold;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Renderizza la tabella avvolta nel contenitore con altezza fissa
    st.markdown(
        f'<div class="table-container">{html_table}</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        f"Righe attualmente visualizzate: {len(st.session_state['dati_accumulatori'])} | Colonne: {num_colonne}"
    )

    if st.session_state["has_more"]:
        if st.button("Carica altre 50 righe"):
            carica_prossime_righe()
            st.rerun()
    else:
        st.info("Tutti i dati disponibili sono stati caricati.")


if st.button("Back to Home Page"):
    st.session_state.clear()
    st.session_state["dati_accumulatori"] = []
    st.session_state["current_offset"] = 0
    st.session_state["has_more"] = True
    st.switch_page("pages/home.py")