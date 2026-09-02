import uuid
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Result of query", layout="wide")
st.title("Result of query")

PAGE_SIZE = 50

# 1. Inizializzazione Session State
if "tutti_i_dati" not in st.session_state:
    st.session_state["tutti_i_dati"] = None
if "pagina_corrente" not in st.session_state:
    st.session_state["pagina_corrente"] = 1
if "query_id" not in st.session_state:
    st.session_state["query_id"] = str(uuid.uuid4())

query_id = st.session_state["query_id"]


def carica_tutti_i_dati():
    """Scarica il dataset mostrando il pulsante di annullamento SOLO durante l'esecuzione."""
    payload = {"parametri": st.session_state.get("pipeline_input")}

    # Creiamo un container temporaneo che sparirà appena i dati saranno pronti
    loading_container = st.empty()

    with loading_container.container():
        st.info("🕒 Elaborazione query in corso...")

        # Pulsante ANNULLA visibile ESCLUSIVAMENTE mentre i dati sono None (in caricamento)
        if st.button("🚫 Annulla la query e torna alla home", key="btn_cancel"):
            try:
                requests.delete(
                    f"http://127.0.0.1:8000/cancel-query/{query_id}"
                )
            except Exception as e:
                st.error(f"Errore durante l'annullamento: {e}")

            st.session_state.clear()
            st.switch_page("pages/home.py")

        # Chiamata HTTP
        try:

            response = requests.post(
                f"http://127.0.0.1:8000/AKI/{query_id}", json=payload
            )

            if response.status_code == 200:
                dati = response.json()
                if dati:
                    st.session_state["tutti_i_dati"] = dati
                    st.session_state["pagina_corrente"] = 1
                else:
                    st.session_state["tutti_i_dati"] = []
            else:
                st.error(
                    f"Errore dal server ({response.status_code}): {response.text}"
                )
                st.session_state["tutti_i_dati"] = []

        except requests.exceptions.RequestException:
            st.error("Richiesta interrotta o errore di connessione.")
            st.session_state["tutti_i_dati"] = []

    # Puliamo il container per far Scomparire il pulsante di annullamento
    loading_container.empty()


# Esecuzione Caricamento (Solo se non abbiamo ancora i dati)
if st.session_state["tutti_i_dati"] is None:
    carica_tutti_i_dati()
    st.rerun()  # Riavvia lo script per aggiornare l'interfaccia senza il loader

# Visualizzazione Dati e Paginazione
if st.session_state["tutti_i_dati"] is not None:

    if len(st.session_state["tutti_i_dati"]) == 0:
        st.warning(
            "Non sono stati trovati pazienti che soddisfano i parametri selezionati."
        )
    else:
        st.success("Dati caricati con successo!")

        tutti_i_dati = st.session_state["tutti_i_dati"]


        totale_righe = len(tutti_i_dati)
        totale_pagine = max(1, (totale_righe + PAGE_SIZE - 1) // PAGE_SIZE)

        pagina = st.session_state["pagina_corrente"]
        start_idx = (pagina - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE

        dati_pagina = tutti_i_dati[start_idx:end_idx]


        df_pagina = pd.DataFrame(dati_pagina)
        df_dati = pd.DataFrame(tutti_i_dati)

        num_colonne = len(df_pagina.columns)
        html_table = df_pagina.to_html(classes="fixed-table", index=False)

        # Style CSS
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

        st.markdown(
            f'<div class="table-container">{html_table}</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            f"Mostrati record {start_idx + 1} - {min(end_idx, totale_righe)} di {totale_righe} | "
            f"Pagina {pagina} di {totale_pagine}"
        )

        # Controlli Paginazione
        col_prev, col_page, col_next, col_csv_all,col_csv_pag ,_ = st.columns([1, 2, 1, 1 ,1,3])

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
                mime="text/csv"
            )
        with col_csv_pag:
            csv_pagina = df_pagina.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Scarica dati {pagina}° pagina",
                data=csv_pagina,
                file_name=f"{pagina}°pagina.csv",
                mime="text/csv"
            )

    # Pulsante per tornare alla home
    st.write("---")
    if st.button("🏠 Torna alla Home Page"):
        st.session_state.clear()
        st.switch_page("pages/home.py")