import streamlit as st
import pandas as pd
import sqlite3

st.title("Quotation Tool")

# DB
conn = sqlite3.connect("quotation.db", check_same_thread=False)

# Load master list
try:
    master_df = pd.read_sql("SELECT * FROM master_items", conn)
except:
    st.error("Master list not found")
    st.stop()

uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity)",
    type=["xlsx"]
)

if uploaded_file is not None:
    quote_df = pd.read_excel(uploaded_file)

    # 🔹 تنظيف أسماء الأعمدة
    quote_df.columns = (
        quote_df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # 🔹 توحيد أسماء الأعمدة
    column_map = {
        "item": "item",
        "items": "item",
        "product": "item",

        "quantity": "quantity",
        "qty": "quantity",
