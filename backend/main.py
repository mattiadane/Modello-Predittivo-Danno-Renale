from backend.schema import PipelineInput
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

import backend.dao as dao

from .connection import get_db

app = FastAPI()


@app.get("/AKI")
def root(
    payload: PipelineInput,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db),
):
    if payload is None or not payload.parametri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun parametro passato.",
        )

    # Genera la query passando limit ed offset
    sql_q = dao.prediction_AKI(payload, limit=limit, offset=offset)

    print("\n" + "=" * 50, flush=True)
    print(f"QUERY GENERATA (LIMIT {limit}, OFFSET {offset}):", flush=True)
    print(sql_q, flush=True)
    print("=" * 50 + "\n", flush=True)

    result = session.execute(text(sql_q)).mappings().all()

    if not result:
        return []

    return [dict(r) for r in result]