import uuid
import pandas as pd
import requests
import streamlit as st

# --- Configurazione Iniziale della Pagina ---
st.set_page_config(page_title="Result of query", layout="wide")
st.title("Result of query")

# Dimensione fissa per la paginazione delle righe nella tabella
PAGE_SIZE = 50

# ---  Inizializzazione dello Stato della Sessione (st.session_state) ---
# Mantiene lo stato tra i vari rerun generati dalle interazioni dell'utente
if "tutti_i_dati" not in st.session_state:
    st.session_state["tutti_i_dati"] = None
if "pagina_corrente" not in st.session_state:
    st.session_state["pagina_corrente"] = 1
if "query_id" not in st.session_state:
    # Identificativo univoco generato per tracciare/annullare la richiesta HTTP specifica
    st.session_state["query_id"] = str(uuid.uuid4())
if "errore_query" not in st.session_state:
    st.session_state["errore_query"] = None

query_id = st.session_state["query_id"]


# --- Funzione per il Recupero Dati ---
def carica_tutti_i_dati():
    """Effettua la chiamata API REST al backend FastAPI per elaborare e scaricare i dati.

    Mostra un feedback visivo e un pulsante di annullamento per la richiesta.
    """
    # Estrazione dei parametri inseriti dall'utente nella home
    payload = {
        "windows": st.session_state.get("pipeline_input", {}).get("windows", []),
        "parametri": st.session_state.get("pipeline_input", {}).get("features", {}),
    }

    # Container temporaneo per la schermata di caricamento
    loading_container = st.empty()

    with loading_container.container():
        st.info("🕒 Elaborazione query in corso...")

        # Pulsante di annullamento: permette di interrompere la query sul server via DELETE
        if st.button("🚫 Annulla la query e torna alla home", key="btn_cancel"):
            try:
                requests.delete(f"http://127.0.0.1:8000/cancel-query/{query_id}")
            except Exception as e:
                st.error(f"Errore durante l'annullamento: {e}")

            st.session_state.clear()
            st.switch_page("pages/home.py")

        # Chiamata HTTP POST sincrona al backend FastAPI
        try:
            response = requests.post(
                f"http://127.0.0.1:8000/AKI/{query_id}", json=payload
            )

            if response.status_code == 200:
                dati = response.json()
                st.session_state["tutti_i_dati"] = dati if dati else []
                st.session_state["pagina_corrente"] = 1
                st.session_state["errore_query"] = None
                esito = True
            else:
                st.session_state["errore_query"] = (
                    f"Errore dal server ({response.status_code}): {response.text}"
                )
                esito = False

        except requests.exceptions.RequestException as e:
            st.session_state["errore_query"] = (
                f"Richiesta interrotta o errore di connessione: {e}"
            )
            esito = False

    # Pulisce l'area di caricamento dopo aver ottenuto la risposta
    loading_container.empty()
    return esito


# --- Controller di Caricamento ---
# Esegue la chiamata al server solo al primo caricamento (quando non ci sono né dati né errori)
if st.session_state["tutti_i_dati"] is None and st.session_state["errore_query"] is None:
    successo = carica_tutti_i_dati()
    if successo:
        st.rerun()

# ---  Gestione degli Errori ---
if st.session_state["errore_query"] is not None:
    st.error(st.session_state["errore_query"])

    col_home, _ = st.columns([1, 4])
    with col_home:
        if st.button("🏠 Torna alla Home Page"):
            st.session_state.clear()
            st.switch_page("pages/home.py")

# ---  Rendering Dati, Tabella Personalizzata e Paginazione ---
elif st.session_state["tutti_i_dati"] is not None:

    if len(st.session_state["tutti_i_dati"]) == 0:
        st.warning(
            "Non sono stati trovati pazienti che soddisfano i parametri selezionati."
        )
    else:
        st.success("Dati caricati con successo!")

        tutti_i_dati = st.session_state["tutti_i_dati"]

        # Calcolo degli indici per lo slicing dei dati (Paginazione lato client)
        totale_righe = len(tutti_i_dati)
        totale_pagine = max(1, (totale_righe + PAGE_SIZE - 1) // PAGE_SIZE)

        pagina = st.session_state["pagina_corrente"]
        start_idx = (pagina - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE

        # Estrazione del sottoinsieme di dati per la pagina attiva
        dati_pagina = tutti_i_dati[start_idx:end_idx]

        df_pagina = pd.DataFrame(dati_pagina)
        df_dati = pd.DataFrame(tutti_i_dati)

        num_colonne = len(df_pagina.columns)
        html_table = df_pagina.to_html(classes="fixed-table", index=False)

        # Iniezione di CSS per rendere la tabella scrollabile con header fisso (sticky)
        st.markdown(
            f"""
            <style>
            .table-container {{
                max-height: 500px;
                overflow-y: auto;
                overflow-x: auto;
                border: 1px solid rgba(250, 250, 250, 0.2);
                border-radius: 6px;
                margin-bottom: 10px;
            }}
            .fixed-table {{
                width: 100% !important;
                min-width: {num_colonne * 140}px;
                table-layout: auto !important;
                border-collapse: collapse;
                font-size: 13px;
            }}
            .fixed-table th, .fixed-table td {{
                min-width: 120px;
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

        # Rendering della tabella HTML all'interno del container con scroll
        st.markdown(
            f'<div class="table-container">{html_table}</div>',
            unsafe_allow_html=True,
        )

        # Dettagli riassuntivi sulla paginazione corrente
        st.caption(
            f"Mostrati record {start_idx + 1} - {min(end_idx, totale_righe)} di {totale_righe} | "
            f"Pagina {pagina} di {totale_pagine}"
        )

        # --- Controlli dell'Interfaccia: Paginazione ed Esportazione CSV ---
        col_prev, col_page, col_next, col_csv_all, col_csv_pag, _ = st.columns([1, 2, 1, 1, 1, 3])

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

        with col_csv_all:
            csv_all = df_dati.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Scarica tutti i dati",
                data=csv_all,
                file_name="allData.csv",
                mime="text/csv",
            )

        with col_csv_pag:
            csv_pagina = df_pagina.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Scarica dati {pagina}° pagina",
                data=csv_pagina,
                file_name=f"{pagina}°pagina.csv",
                mime="text/csv",
            )

    # Pulsante per resettare lo stato e rientrare alla pagina principale
    st.write("---")
    if st.button("🏠 Torna alla Home Page"):
        st.session_state.clear()
        st.switch_page("pages/home.py")