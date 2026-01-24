import streamlit as st
import pandas as pd
import os
import pdfplumber
from thefuzz import process, fuzz

st.set_page_config(page_title="Quotation System", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ---------------------------
# تحميل الماستر
# ---------------------------
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)

    df = pd.read_excel(MASTER_FILE)
    df.columns = df.columns.str.strip()
    return df


master_df = load_master()
master_items = master_df["Item"].astype(str).tolist() if not master_df.empty else []


# ---------------------------
# PDF Reader
# ---------------------------
def read_pdf(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                rows.extend(table[1:])

    return pd.DataFrame(rows)


# ---------------------------
# Fuzzy Match
# ---------------------------
def match_ite_
