import streamlit as st
import pandas as pd
import sqlite3

st.title("Master List")

uploaded = st.file_uploader(
    "Upload Master List Excel",
    type=["xlsx"]
)

if uploaded:
    df = pd.read_excel(uploaded)

    required_cols = ["Item", "Unit", "Unit_Price", "VAT_Percent"]
    df.columns = df.columns.str.strip()

    if not all(col in df.columns for col in required_cols):
        st.error("Excel must contain columns: Item, Unit, Unit_Price, VAT_Percent")
        st.stop()

    st.dataframe(df)

    if st.button("Save Master List"):
        conn = sqlite3.connect("master.db")
        df.to_sql("master_list", conn, if_exists="replace", index=False)
        conn.close()
        st.success("Master List saved successfully ✅")

