import os
import dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker

dotenv.load_dotenv()

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DATABASE = os.getenv("DATABASE")
SCHEMA = os.getenv("SCHEMA")
PASSWORD = os.getenv("PASSWORD")



url = URL.create(
    drivername="postgresql+psycopg2",
    username='Mattia Danese',
    password=PASSWORD,
    host=HOST,
    port=PORT,
    database=DATABASE,
)


engine = create_engine(
    url,
    pool_size=5,
    max_overflow=10,
    connect_args={"options": f"-c search_path={SCHEMA}"}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
