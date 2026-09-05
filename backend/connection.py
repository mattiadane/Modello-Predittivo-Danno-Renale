import os
from pathlib import Path
import dotenv
from sqlalchemy import URL, create_engine, event
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
SCHEMA = os.getenv("SCHEMA", "public")
USERNAME = os.getenv("USERNAME", "Username")  # Se necessario leggi anche l'user da env
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
    port=int(PORT) if PORT else 5433,
    database=DATABASE,
)

engine = create_engine(
    url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,      # Prova la connessione prima di usarla e la ricrea se è morta
    pool_recycle=1800,       # Ricicla le connessioni ogni 30 minuti (1800 sec)
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,       # Invia un ping dopo 30s di inattività
        "keepalives_interval": 10,   # Riprova ogni 10s se non riceve risposta
        "keepalives_count": 5        # Considera morta la connessione dopo 5 tentativi
    }
)

@event.listens_for(engine, "checkout")
def set_search_path(dbapi_connection, connection_record, connection_proxy):
    with dbapi_connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{SCHEMA}", public;')

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()