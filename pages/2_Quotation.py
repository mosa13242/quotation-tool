import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.set_page_config(page_title="Quotation", layout="wide")

st.title("Quotation")

# ======================
# Database
# ======================
conn = sqlite3.connect("quotation.db", check_same_thread=False)

master_df = pd.read_sql(
    "SELECT Item, Unit, Unit_Price, VAT_Percent FROM master_items",
    conn
)

# ======================
# Upload file
# ======================
uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity)",
    type=["xlsx"]
)

if uploaded_file is not None:
    quote_df = pd.read_excel(uploaded_file)
    quote_df.columns = quote_df.columns.str.strip()

    if "Item" not in quote_df.columns or "Quantity" not in quote_df.columns:
        st.error("Excel must contain Item and Quantity columns")
        st.stop()

    quote_df["Quantity"] = pd.to_numeric(
        quote_df["Quantity"],
        errors="coerce"
    ).fillna(0)

    merged = pd.merge(
        quote_df,
        master_df,
        on="Item",
        how="left"
    )

    merged["Unit_Price"] = pd.to_numeric(
        merged["Unit_Price"],
        errors="coerce"
    ).fillna(0)

    merged["VAT_Percent"] = pd.to_numeric(
        merged["VAT_Percent"],
        errors="coerce"
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

    st.subheader("Quotation Details")
    st.dataframe(merged, use_container_width=True)

    total_before = merged["Total_Before_VAT"].sum()
    total_vat = merged["VAT_Amount"].sum()
    grand_total = merged["Total_After_VAT"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Before VAT", f"{total_before:,.2f}")
    c2.metric("VAT Amount", f"{total_vat:,.2f}")
    c3.metric("Grand Total", f"{grand_total:,.2f}")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        merged.to_excel(writer, index=False)

    st.download_button(
        "Download Quotation Excel",
        data=output.getvalue(),
        file_name="Quotation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
