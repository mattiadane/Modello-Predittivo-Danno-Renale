import os
from pathlib import Path
import dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker

# 1. Trova la cartella 'backend' (dove risiede connection.py e il .env)
BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"

# 2. Carica il file .env dal percorso esatto dentro backend/
dotenv.load_dotenv(dotenv_path=ENV_PATH, override=True)

# 3. Leggi le variabili
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DATABASE = os.getenv("DATABASE")
SCHEMA = os.getenv("SCHEMA")
PASSWORD = os.getenv("PASSWORD")


if not HOST:
    raise ValueError(
        f"ERRORE: Impossibile leggere HOST. Verificare che {ENV_PATH} contenga 'HOST=...'"
    )

url = URL.create(
    drivername="postgresql+psycopg2",
    username="Mattia Danese",
    password=PASSWORD,
    host=HOST,
    port=PORT,
    database=DATABASE,
)

engine = create_engine(
    url,
    pool_size=5,
    max_overflow=10,
    connect_args={"options": f"-c search_path={SCHEMA}"},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()