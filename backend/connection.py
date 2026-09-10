"""
Modulo per la gestione della connessione al database PostgreSQL tramite SQLAlchemy.

Si occupa di:
- Caricare le variabili d'ambiente dal file `.env`.
- Costruire l'URL di connessione al database.
- Configurare l'engine SQLAlchemy con connessioni resilienti (pooling e keepalives).
- Impostare lo `search_path` di PostgreSQL dynamicamente al checkout di una connessione.
- Fornire la dependency `get_db()` per la gestione del ciclo di vita della sessione ORM.
"""

import os
from pathlib import Path
import dotenv
from sqlalchemy import URL, create_engine, event
from sqlalchemy.orm import sessionmaker

# --- CONFIGURAZIONE PERCORSI E AMBIENTE ---

# Individua la cartella di radice del modulo backend (dove risiede connection.py)
BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"

# Carica le variabili d'ambiente dal file .env (override=True forza il ricaricamento)
dotenv.load_dotenv(dotenv_path=ENV_PATH, override=True)

# Lettura e riassociazione delle variabili d'ambiente
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DATABASE = os.getenv("DATABASE")
SCHEMA = os.getenv("SCHEMA", "public")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Controllo difensivo per la variabile critica HOST
if not HOST:
    raise ValueError(
        f"ERRORE: Impossibile leggere HOST. Verificare che {ENV_PATH} contenga 'HOST=...'"
    )

# --- COSTRUZIONE URL E ENGINE SQLALCHEMY ---

# Genera in modo sicuro l'URL di connessione per il driver PostgreSQL
url = URL.create(
    drivername="postgresql+psycopg2",
    username=USERNAME,
    password=PASSWORD,
    host=HOST,
    port=int(PORT) if PORT else 5433,
    database=DATABASE,
)

# Creazione dell'Engine SQLAlchemy con strategie di gestione del Connection Pool
engine = create_engine(
    url,
    pool_size=5,  # Numero di connessioni mantenute permanentemente aperte nel pool
    max_overflow=10,  # Numero massimo di connessioni extra temporanee oltre pool_size
    pool_pre_ping=True,  # Verifica che la connessione sia ancora attiva prima di erogarla
    pool_recycle=1800,  # Forza il riciclo/ricreazione delle connessioni dopo 30 minuti (1800s)
    connect_args={
        # Configurazione TCP Keepalive nativa di psycopg2 per prevenire disconnessioni silenziose
        "keepalives": 1,
        "keepalives_idle": 30,  # Invia un pacchetto di ping TCP dopo 30s di inattività
        "keepalives_interval": 10,  # Intervallo di 10s tra i tentativi di ping
        "keepalives_count": 5  # Considera la connessione caduta dopo 5 risposte mancate
    }
)


# --- HOOK EVENTI DATABASE ---

@event.listens_for(engine, "checkout")
def set_search_path(dbapi_connection, connection_record, connection_proxy):
    """
    Hook eseguito ogni volta che una connessione viene prelevata (checkout) dal pool.
    Imposta lo 'search_path' di PostgreSQL per dare priorità allo schema configurato.
    """
    with dbapi_connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{SCHEMA}", public;')


# --- SESSIONI E DEPENDENCY PROVIDER ---

# Factory per la creazione delle sessioni ORM
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """
    Generator/Dependency per il ciclo di vita della sessione di database.

    Apre una nuova sessione per ciascuna richiesta HTTP e ne garantisce
    la chiusura corretta (release della connessione al pool) al termine.

    Yields:
        Session: Istanza attiva di SQLAlchemy Session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()