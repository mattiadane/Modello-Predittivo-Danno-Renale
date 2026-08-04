from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from streamlit import status
from .connection import  get_db
from backend.schema import  PipelineInput
import  backend.dao as dao




app = FastAPI()

@app.get("/AKI")
async def root(session : Session = Depends(get_db), payload : PipelineInput = None) :
  if payload is None:
       raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Nessun parametro passato."
      )

  sql_q = dao.prediction_AKI(payload)
  print("\n" + "=" * 50, flush=True)
  print("QUERY GENERATA CON SUCCESSO:", flush=True)
  print(sql_q, flush=True)
  print("=" * 50 + "\n", flush=True)
  result = session.execute(text(sql_q)).mappings().all()
  if not result:
    return {
      "status": "empty",
      "message": "Nessuna misurazione trovata nella finestra temporale.",
      "data": []
    }

  return [ dict(r) for r in result]


