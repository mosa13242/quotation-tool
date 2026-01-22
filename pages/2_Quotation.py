import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.set_page_config(page_title="Quotation", layout="wide")

st.title("Quotation")

# -----------------------
# Database connection
# -----------------------
conn = sqlite3.connect("quotation.db", check_same_thread=False)

# -----------------------
# Load Master List
# -----------------------
master_df = pd.read_sql("SELECT * FROM master_items", conn)

# -----------------------
# Upload quotation Excel
# Required columns: Item | Quantity
# -----------------------
uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity)",
    type=["xlsx"]
)

if uploaded_file:
    quote_df = pd.read_excel(uploaded_file)

    # Normalize column names
    quote_df.columns = quote_df.columns.str.strip()

    if "Item" not in quote_df.columns or "Quantity" not in quote_df.columns:
        st.error("Excel must contain columns: Item , Quantity")
        st.stop()

    # Ensure Quantity numeric
    quote_df["Quantity"] = pd.to_numeric(
        quote_df["Quantity"], errors="coerce"
    ).fillna(0)

    # -----------------------
    # Merge with master list
    # -----------------------
    merged = pd.merge(
        quote_df,
        master_df,
        on="Item",
        how="left"
    )

    # Fill missing values
    merged["Unit_Price"] = pd.to_numeric(
        merged["Unit_Price"], errors="coerce"
    ).fillna(0)

    merged["VAT_Percent"] = pd.to_numeric(
        merged["VAT_Percent"], errors="coerce"
    ).fillna(0)

    # -----------------------
    # Calculations
    # -----------------------
    merged["Total_Before_VAT"] = (
        merged["Quantity"] * merged["Unit_Price"]
    )

    merged["VAT_Amount"] = (
        merged["Total_Before_VAT"] * merged["VAT_Percent"] / 100
    )

    merged["Total_After_VAT"] = (
        merged["Total_Before_VAT"] + merged["VAT_Amount"]
    )

    # -----------------------
    # Display table
    # -----------------------
    st.subheader("Quotation Details")
    st.dataframe(merged, use_container_width=True)

    # -----------------------
    # Totals
    # -----------------------
    total_before_vat = merged["Total_Before_VAT"].sum()
    vat_amount = merged["VAT_Amount"].sum()
    grand_total = merged["Total_After_VAT"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Before VAT", f"{total_before_vat:,.2f}")
    col2.metric("VAT Amount", f"{vat_amount:,.2f}")
    col3.metric("Grand Total", f"{grand_total:,.2f}")

    # -----------------------
    # Download Excel
    # -----------------------
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        merged.to_excel(
            writer,
            index=False,
            sheet_name="Quotation"
        )

    st.download_button(
        label="Download Quotation Excel",
