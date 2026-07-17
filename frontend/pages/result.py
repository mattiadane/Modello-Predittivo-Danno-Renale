import streamlit as st

st.title("Result of query")




if "state" in st.session_state:
    st.dataframe(st.session_state.state["example"])




if st.button("Back to Home Page"):
    st.session_state.clear()
    st.switch_page("pages/home.py")