import streamlit as st
import pandas as pd
import sqlite3

st.title("📦 Master List")

uploaded_file = st.file_uploader(
    "Upload Master List Excel",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.dataframe(df)

    if st.button("Save Master List"):
        conn = sqlite3.connect("quotation.db")
        df.to_sql("master_items", conn, if_exists="replace", index=False)
        conn.close()
        st.success("Master List saved successfully ✅")

