import streamlit as st
from sqlalchemy import text

class Connection:

    def __init__(self):
        self.conn = st.connection("mydb", type="sql")

        self.schema = st.secrets["connections"]["mydb"].get("schema", "public")

        # 3. FORZA lo schema con una transazione esplicita (Risolve il problema del reset)
        with self.conn.engine.connect() as connection:
            with connection.begin():
                connection.execute(text(f"SET search_path TO {self.schema};"))



    def query(self, query):
        return self.conn.query(query)