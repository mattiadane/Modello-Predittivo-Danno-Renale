import streamlit as st

class Connection:

    def __init__(self):
        conn = st.connection("mydb", type="sql")