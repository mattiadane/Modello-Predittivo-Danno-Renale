from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from .connection import  get_db

app = FastAPI()


@app.get("/patient")
async def root(session : Session = Depends(get_db)):
  result =  session.execute(text("SELECT * FROM patients LIMIT 10")).fetchall()

  if not result:
    return {"message": "No patient found"}

  return [dict(r._mapping) for r in result]