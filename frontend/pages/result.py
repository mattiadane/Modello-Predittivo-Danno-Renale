import streamlit as st

st.title("Result of query")


if "state" in st.session_state:
    st.dataframe(st.session_state.state["example"])