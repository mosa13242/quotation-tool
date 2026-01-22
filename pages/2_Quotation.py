import streamlit as st
import pandas as pd
import sqlite3
import pdfplumber

st.title("Quotation Tool")
st.write("Upload Excel or PDF file (Item + Quantity)")

# =========================
# Load Master List
# =========================
try:
    conn = sqlite3.connect("master.db")
    master_df = pd.read_sql("SELECT * FROM master_list", conn)
    conn.close()
except:
    st.error("Master list not found. Upload it first.")
    st.stop()

master_df.columns = master_df.columns.str.strip()
master_df["Item"] = master_df["Item"].astype(str).str.strip()

# =========================
# Upload File
# =========================
uploaded = st.file_uploader(
    "Upload Quotation File",
    type=["xlsx", "pdf"]
)

if uploaded:
    # -------- Excel --------
    if uploaded.name.endswith(".xlsx"):
        quote_df = pd.read_excel(uploaded)

    # -------- PDF --------
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
    # CLEAN COLUMNS (CRITICAL)
    # =========================
    quote_df.columns = (
        quote_df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "")
    )

    # =========================
    # Detect Quantity Column
    # =========================
    qty_col = None
    for col in quote_df.columns:
        if "qty" in col or "quantity" in col:
            qty_col = col
            break

    if qty_col is None:
        st.error("Quantity column not found (Qty / Quantity)")
        st.write("Detec

