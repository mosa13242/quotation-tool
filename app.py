import streamlit as st

st.set_page_config(page_title="Quotation Tool", layout="wide")

st.sidebar.title("app")
st.sidebar.page_link("pages/1_Master_List.py", label="Master List")
st.sidebar.page_link("pages/2_Quotation.py", label="Quotation")

st.title("Quotation Tool")
st.write("Use the sidebar to navigate")




