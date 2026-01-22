import streamlit as st
import pandas as pd
import sqlite3

st.title("Quotation Tool")

# ======================
# Database connection
# ======================
conn = sqlite3.connect("quotation.db", check_same_thread=False)

try:
    master_df = pd.read_sql("SELECT * FROM master_items", conn)
except:
    st.error("Master list not found in database")
    st.stop()

# ======================
# File uploader
# ======================
uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity)",
    type=["xlsx", "pdf"]
)

if uploaded_file is not None:
    quote_df = pd.read_excel(uploaded_file)

    # ======================
    # Clean column names
    # ======================
    quote_df.columns = (
        quote_df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # ======================
    # Column mapping ✅ (مقفول صح)
    # ======================
    column_map = {
        "item": "item",
        "items": "item",
        "product": "item",

        "quantity": "quantity",
        "qty": "quantity",
        "qte": "quantity"
    }

    quote_df = quote_df.rename(columns=column_map)

    # ======================
    # Validation
    # ======================
    if "item" not in quote_df.columns or "quantity" not in quote_df.columns:
        st.error(
            "Excel must contain columns: Item & Quantity\n\n"
            f"Detected columns: {list(quote_df.columns)}"
        )
        st.stop()

    # ======================
    # Merge with master list
    # ======================
    result = quote_df.merge(
        master_df,
        left_on="item",
        right_on="Item",
        how="left"
    )

    # ======================
    # Calculations
    # ======================
    result["quantity"] = pd.to_numeric(result["quantity"], errors="coerce").fillna(0)
    result["Unit_Price"] = pd.to_numeric(result["Unit_Price"], errors="coerce").fillna(0)
    result["VAT_Percent"] = pd.to_numeric(result["VAT_Percent"], errors="coerce").fillna(0)

    result["Total_Before_VAT"] = result["quantity"] * result["Unit_Price"]
    result["VAT_Amount"] = result["Total_Before_VAT"] * result["VAT_Percent"] / 100
    result["Total_After_VAT"] = result["Total_Before_VAT"] + result["VAT_Amount"]

    # ======================
    # Output
    # ======================
    st.subheader("Quotation Result")
    st.dataframe(result)

    st.subheader("Totals")
    st.metric("Total Before VAT", round(result["Total_Before_VAT"].sum(), 2))
    st.metric("VAT Amount", round(result["VAT_Amount"].sum(), 2))
    st.metric("Grand Total", round(result["Total_After_VAT"].sum(), 2))
