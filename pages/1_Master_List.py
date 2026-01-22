import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Master List", layout="wide")
st.title("Master List")

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# CREATE TABLE (VERY IMPORTANT)
cursor.execute("""
CREATE TABLE IF NOT EXISTS master_items (
    Item TEXT PRIMARY KEY,
    Unit TEXT,
    Unit_Price REAL,
    VAT_Percent REAL
)
""")
conn.commit()

uploaded_file = st.file_uploader(
    "Upload Master List Excel",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    expected_cols = {"Item", "Unit", "Unit_Price", "VAT_Percent"}
    if not expected_cols.issubset(df.columns):
        st.error("Excel columns must be: Item, Unit, Unit_Price, VAT_Percent")
        st.stop()

    st.dataframe(df)

    if st.button("Save Master List"):
        df.to_sql("master_items", conn, if_exists="replace", index=False)
        st.success("Master List saved successfully ✅")

