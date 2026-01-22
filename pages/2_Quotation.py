import streamlit as st
import pandas as pd
import sqlite3
import pdfplumber

st.title("Quotation Tool")
st.write("Upload Excel or PDF file (Item + Quantity)")

# =========================
# Load Master List from DB
# =========================
try:
    conn = sqlite3.connect("master.db")
    master_df = pd.read_sql("SELECT * FROM master_list", conn)
    conn.close()
except:
    st.error("Master list not found. Upload it first.")
    st.stop()

if master_df.empty:
    st.error("Master list is empty.")
    st.stop()

master_df["Item"] = master_df["Item"].astype(str).str.strip()

# =========================
# Upload Quotation File
# =========================
uploaded = st.file_uploader(
    "Upload Quotation File",
    type=["xlsx", "pdf"]
)

if uploaded:
    # ---------- Excel ----------
    if uploaded.name.endswith(".xlsx"):
        quote_df = pd.read_excel(uploaded)

    # ---------- PDF ----------
    else:
        rows = []
        with pdfplumber.open(uploaded) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    rows.extend(table)

        if not rows:
            st.error("Could not read table from PDF")
            st.stop()

        quote_df = pd.DataFrame(rows[1:], columns=rows[0])

    # =========================
    # Clean & Validate
    # =========================
    quote_df.columns = quote_df.columns.astype(str).str.strip()

    if "Item" not in quote_df.columns or "Quantity" not in quote_df.columns:
        st.error("File must contain columns: Item and Quantity")
        st.stop()

    quote_df["Item"] = quote_df["Item"].astype(str).str.strip()
    quote_df["Quantity"] = pd.to_numeric(quote_df["Quantity"], errors="coerce").fillna(0)

    # =========================
    # Merge with Master
    # =========================
    result = quote_df.merge(master_df, on="Item", how="left")

    if result["Unit_Price"].isna().any():
        st.warning("Some items were not found in master list")

    result["Subtotal"] = result["Quantity"] * result["Unit_Price"]
    result["VAT"] = result["Subtotal"] * (result["VAT_Percent"] / 100)
    result["Total"] = result["Subtotal"] + result["VAT"]

    st.dataframe(result)

    st.subheader("Grand Total")
    st.success(f"{result['Total'].sum():.2f}")
