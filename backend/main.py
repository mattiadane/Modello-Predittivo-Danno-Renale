from sqlalchemy.exc import OperationalError, DBAPIError

from backend.schema import PipelineInput
from fastapi import Depends, FastAPI, HTTPException, Query, status, params
from sqlalchemy import text
from sqlalchemy.orm import Session

import backend.dao as dao

from .connection import get_db


active_queries: dict[str, int] = {}
app = FastAPI()


@app.post("/AKI/{query_id}")
def root(
    query_id : str,
    payload: PipelineInput,
    session: Session = Depends(get_db),
):


    db_pid = session.execute(text(dao.get_PID())).scalar()

    if db_pid is not None:
        active_queries[query_id] = int(db_pid)


    try :
        if payload is None or not payload.parametri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessun parametro passato.",
            )

        # Genera la query passando limit ed offset
        sql_q = dao.prediction_AKI(payload)

        print("\n" + "=" * 50, flush=True)
        print(f"QUERY GENERATA :", flush=True)
        print(sql_q, flush=True)
        print("=" * 50 + "\n", flush=True)

        result = session.execute(text(sql_q)).mappings().all()

        if not result:
            return []

        return [dict(r) for r in result]

    except (OperationalError, DBAPIError) as e:

        # Se l'errore è dovuto alla cancellazione da parte del DB, gestiscilo pulitamente
        if "canceling statement due to user request" in str(e).lower():
            print(f"Query {query_id} (PID: {db_pid}) interrotta dall'utente.", flush=True)
            session.rollback()  # Annulla lo stato della transazione SQLAlchemy


            return {"status": "cancelled", "message": "Query interrotta con successo."}

        # Se si tratta di un altro errore di DB reale viene riportato
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore del database: {str(e)}",
        )
    finally:
        active_queries.pop(query_id,None)


@app.post("/cancel-query/{query_id}")
def cancel_query(query_id : str, session: Session = Depends(get_db)):

    if params is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nella richiesta",
        )


    db_pid = active_queries.get(query_id)

    if db_pid:
        # Invia il comando KILL/CANCEL a Postgres
        session.execute(text(f"SELECT pg_cancel_backend({db_pid})"))
        session.commit()
        return {"status": "Query interrotta"}

    return {"status": "Query non trovata"}
