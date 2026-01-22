import streamlit as st
import pandas as pd
import io
import pdfplumber

st.set_page_config(page_title="Quotation Tool", layout="wide")

# -----------------------
# Session State
# -----------------------
if "master_df" not in st.session_state:
    st.session_state.master_df = None

# -----------------------
# Helpers
# -----------------------
def read_pdf_items(pdf_file):
    rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for r in table[1:]:
                    if len(r) >= 2:
                        rows.append({
                            "Item": str(r[0]).strip(),
                            "Quantity": float(r[1]) if str(r[1]).replace('.', '').isdigit() else 1
                        })
    return pd.DataFrame(rows)

# -----------------------
# UI
# -----------------------
menu = st.sidebar.radio("Menu", ["Master List", "Quotation"])

# =======================
# MASTER LIST
# =======================
if menu == "Master List":
    st.title("Master List")

    file = st.file_uploader("Upload Master List Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()

        required = {"Item", "Unit", "Unit_Price", "VAT_Percent"}
        if not require
