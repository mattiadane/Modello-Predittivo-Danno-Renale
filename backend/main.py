from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from streamlit import status

from .connection import  get_db
from schema import  PipelineInput
import  dao




app = FastAPI()


@app.get("/patient")
async def root(session : Session = Depends(get_db)):
  result =  session.execute(text("SELECT * FROM patients LIMIT 10")).fetchall()

  if not result:
    return {"message": "No patient found"}

  return [dict(r._mapping) for r in result]


@app.get("/AKI")
async def root(session : Session = Depends(get_db), payload : PipelineInput = None) :
  if payload is None:
       raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Nessun parametro passato."
      )

  result = session.execute(dao.prediction_AKI(payload)).mappings().all()
  if not result:
    return {
      "status": "empty",
      "message": "Nessuna misurazione trovata nella finestra temporale.",
      "data": []
    }

  return [ dict(r) for r in result]


