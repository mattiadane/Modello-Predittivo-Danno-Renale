"""
API Service per la gestione delle query di predizione AKI (Acute Kidney Injury).

Fornisce endpoint per:
- Eseguire query complesse registrando il Process ID (PID) del database per eventuale annullamento.
- Annullare query in esecuzione inviando un comando di terminazione direttamente al DB.
- Recuperare dati ausiliari (es. eventi di input).
"""

from sqlalchemy.exc import OperationalError, DBAPIError
from backend.schema import PipelineInput
from fastapi import Depends, FastAPI, HTTPException, status, params
from sqlalchemy import text
from sqlalchemy.orm import Session

import backend.dao as dao
from .connection import get_db

# Dizionario globale in-memory per tracciare le query attive:
# Mappa l'identificativo client/richiesta (query_id) al Process ID del database (PID)
active_queries: dict[str, int] = {}

# Inizializzazione dell'applicazione FastAPI
app = FastAPI()


@app.post("/AKI/{query_id}")
def root(
        query_id: str,
        payload: PipelineInput,
        session: Session = Depends(get_db),
):
    """
    Genera ed esegue una query SQL di predizione AKI in base alla configurazione ricevuta.

    Mantiene una traccia del PID della connessione SQL corrente per consentire la cancellazione 
    asincrona da un altro endpoint. Gestisce in modo graceful le interruzioni manuali.
    """
    # Recupera il PID del processo PostgreSQL associato alla sessione corrente
    db_pid = session.execute(text(dao.get_PID())).scalar()

    # Salva la mappa query_id -> PID per consentire l'eventuale cancellazione
    if db_pid is not None:
        active_queries[query_id] = int(db_pid)

    try:
        # Validazione basilare del payload di input
        if payload is None or not payload.parametri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessun parametro passato.",
            )

        # Genera la query SQL dinamica partendo dagli schemi definiti nel payload
        sql_q = dao.prediction_AKI(payload)

        # Logging della query generata sul terminale
        print("\n" + "=" * 50, flush=True)
        print(f"QUERY GENERATA :", flush=True)
        print(sql_q, flush=True)
        print("=" * 50 + "\n", flush=True)

        # Esegue la query trasformando i risultati in dizionari
        result = session.execute(text(sql_q)).mappings().all()

        if not result:
            return []

        return [dict(r) for r in result]

    except (OperationalError, DBAPIError) as e:
        # Intercetta il segnale di cancellazione inviato dal DB (pg_cancel_backend / pg_terminate_backend)
        if "canceling statement due to user request" in str(e).lower():
            print(f"Query {query_id} (PID: {db_pid}) interrotta dall'utente.", flush=True)
            session.rollback()  # Annulla lo stato transazionale pendente a causa dell'errore

            return {"status": "cancelled", "message": "Query interrotta con successo."}

        # Gestione di altri errori generici/critici del database
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore del database: {str(e)}",
        )
    finally:
        # Rimuove l'entry del PID dal registro in memoria a fine esecuzione (sia in successo che errore)
        active_queries.pop(query_id, None)


@app.delete("/cancel-query/{query_id}")
def cancel_query(query_id: str, session: Session = Depends(get_db)):
    """
    Interrompe l'esecuzione di una query in corso dato il suo query_id.

    Cerca il PID PostgreSQL associato nel registro locale e invia un comando 
    di abort (kill/cancel) al database server.
    """
    # Controllo difensivo sui parametri
    if params is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nella richiesta",
        )

    # Recupera il PID associato al query_id fornito
    db_pid = active_queries.get(query_id)

    if db_pid:
        # Esegue la query DAO che chiama pg_cancel_backend() o pg_terminate_backend()
        session.execute(text(dao.kill_query(db_pid)))
        session.commit()
        return {"status": "Query interrotta"}

    return {"status": "Query non trovata"}


@app.get("/inputevents")
def get_inputevents(session: Session = Depends(get_db)):
    """
    Recupera l'elenco  di tutti gli eventi di input registrati nel database.
    """
    sql = dao.get_inputevents()

    result = session.execute(text(sql)).mappings().all()

    if not result:
        return []

    return [dict(r) for r in result]