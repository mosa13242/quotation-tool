import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.title("Quotation")

conn = sqlite3.connect("quotation.db", check_same_thread=False)

try:
    master_df = pd.read_sql("SELECT * FROM master_items", conn)
except:
    st.error("Master list not found")
    st.stop()

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Item" not in df.columns or "Quantity" not in df.columns:
        st.error("Excel must contain Item and Quantity columns")
        st.stop()

    result = df.merge(master_df, on="Item", how="left")

    result["Quantity"] = pd.to_numeric(result["Quantity"], errors="coerce").fillna(0)
    result["Unit_Price"] = pd.to_numeric(result["Unit_Price"], errors="coerce").fillna(0)
    result["VAT_Percent"] = pd.to_numeric(result["VAT_Percent"], errors="coerce").fillna(0)

    result["Total_Before_VAT"] = result["Quantity"] * result["Unit_Price"]
    result["VAT_Amount"] = result["Total_Before_VAT"] * result["VAT_Percent"] / 100
    result["Total_After_VAT"] = result["Total_Before_VAT"] + result["VAT_Amount"]

    st.dataframe(result)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result.to_excel(writer, index=False)

    st.download_button(
        "Download Quotation Excel",
        output.getvalue(),
        file_name="Quotation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
