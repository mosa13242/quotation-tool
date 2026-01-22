import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.set_page_config(page_title="Quotation", layout="wide")
st.title("Quotation")

# ---------------------------
# DB CONNECTION
# ---------------------------
conn = sqlite3.connect("quotation.db", check_same_thread=False)

# ---------------------------
# LOAD MASTER LIST
# ---------------------------
try:
    master_df = pd.read_sql("SELECT * FROM master_items", conn)
except Exception as e:
    st.error("Master list not found. Please upload Master List first.")
    st.stop()

# Normalize column names
master_df.columns = master_df.columns.str.strip()

# ---------------------------
# UPLOAD QUOTATION FILE
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity)",
    type=["xlsx"]
)

if uploaded_file:
    quote_df = pd.read_excel(uploaded_file)
    quote_df.columns = quote_df.columns.str.strip()

    # ---------------------------
    # VALIDATION
    # ---------------------------
    required_cols = ["Item", "Quantity"]
    missing = [c for c in required_cols if c not in quote_df.columns]

    if missing:
        st.error(f"Missing columns in Excel: {missing}")
        st.stop()

    # Convert Quantity to numeric
    quote_df["Quantity"] = pd.to_numeric(
        quote_df["Quantity"], errors="coerce"
    ).fillna(0)

    # ---------------------------
    # MERGE WITH MASTER
    # ---------------------------
    merged = pd.merge(
        quote_df,
        master_df,
        on="Item",
        how="left"
    )

    if merged["Unit_Price"].isna().any():
        st.warning("Some items were not found in Master List")

    # ---------------------------
    # CALCULATIONS
    # ---------------------------
    merged["Unit_Price"] = pd.to_numeric(
        merged["Unit_Price"], errors="coerce"
    ).fillna(0)

    merged["VAT_Percent"] = pd.to_numeric(
        merged["VAT_Percent"], errors="coerce"
    ).fillna(0)

    merged["Total_Before_VAT"] = (
        merged["Quantity"] * merged["Unit_Price"]
    )

    merged["VAT_Amount"] = (
        merged["Total_Before_VAT"] * merged["VAT_Percent"] / 100
    )

    merged["Total_After_VAT"] = (
        merged["Total_Before_VAT"] + merged["VAT_Amount"]
    )

    # ---------------------------
    # DISPLAY TABLE
    # ---------------------------
    st.subheader("Quotation Details")
    st.dataframe(merged, use_container_width=True)

    # ---------------------------
    # TOTALS
    # ---------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Before VAT",
            f"{merged['Total_Before_VAT'].sum():,.2f}"
        )

    with col2:
        st.metric(
            "VAT Amount",
            f"{merged['VAT_Amount'].sum():,.2f}"
        )

    with col3:
        st.metric(
            "Grand Total",
            f"{merged['Tota]()
