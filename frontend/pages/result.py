import pandas as pd
import requests
import streamlit as st

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
        # Passiamo limit=50 e l'offset corrente come Query Parameters
        params = {"limit": 50, "offset": st.session_state["current_offset"]}

        response = requests.get(
            "http://127.0.0.1:8000/AKI", json=payload, params=params
        )

        if response.status_code == 200:
            nuove_righe = response.json()

            if nuove_righe:
                # Accumuliamo le nuove righe
                st.session_state["dati_accumulatori"].extend(nuove_righe)
                st.session_state["current_offset"] += len(nuove_righe)

                # Se riceviamo meno di 50 righe, abbiamo raggiunto la fine dei dati
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


# 3. Primo caricamento automatico (solo se la lista è ancora vuota)
if not st.session_state["dati_accumulatori"] and st.session_state["has_more"]:
    carica_prossime_righe()

# 4. Visualizzazione della tabella e dei controlli
if st.session_state["dati_accumulatori"]:
    st.success("Dati caricati con successo!")

    df = pd.DataFrame(st.session_state["dati_accumulatori"])
    st.dataframe(df, use_container_width=True)

    st.caption(
        f"Righe attualmente visualizzate: {len(st.session_state['dati_accumulatori'])}"
    )

    # Pulsante per richiedere il blocco successivo di 50 righe
    if st.session_state["has_more"]:
        if st.button("Carica altre 50 righe"):
            carica_prossime_righe()
            st.rerun()
    else:
        st.info("Tutti i dati disponibili sono stati caricati.")

if st.button("Back to Home Page"):
    st.session_state.clear()
    st.switch_page("pages/home.py")