import streamlit as st
import pandas as pd
import pdfplumber
import io

st.set_page_config(page_title="Quotation Tool", layout="wide")

# ======================
# Sidebar Navigation
# ======================
page = st.sidebar.radio("Menu", ["Master List", "Quotation"])

# ======================
# Helper Functions
# ======================
def clean_columns(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace(" ", "_")
    )
    return df


def read_pdf_table(uploaded_file):
    rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table[1:]:
                    rows.append(row)

    if not rows:
        return None

    df = pd.DataFrame(rows, columns=["Item", "Quantity"])
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1)
    return df


# ======================
# Master List Page
# ======================
if page == "Master List":
    st.title("Master List")

    uploaded_master = st.file_uploader(
        "Upload Master List Excel",
        type=["xlsx"]
    )

    if uploaded_master:
        df = pd.read_excel(uploaded_master)
        df = clean_columns(df)

        required = {"Item", "Unit", "Unit_Price", "VAT_Percent"}

        if not required.issubset(df.columns):
            st.error("Excel must contain: Item, Unit, Unit_Price, VAT_Percent")
        else:
            st.dataframe(df, use_container_width=True)

            if st.button("Save Master List"):
                st.session_state.master_df = df
                st.success("Master List saved successfully ✅")


# ======================
# Quotation Page
# ======================
if page == "Quotation":
    st.title("Quotation Tool")
    st.write("Upload Excel or PDF file (Item + Quantity) to generate quotation")

    if "master_df" not in st.session_state:
        st.error("Please upload and save Master List first.")
        st.stop()

    uploaded_quote = st.file_uploader(
        "Upload Quotation File (Excel or PDF)",
        type=["xlsx", "pdf"]
    )

    if uploaded_quote:
        if uploaded_quote.name.endswith(".pdf"):
            st.info("Reading PDF file...")
            quote_df = read_pdf_table(uploaded_quote)
        else:
            quote_df = pd.read_excel(uploaded_quote)
            quote_df = clean_columns(quote_df)

        if quote_df is None:
            st.error("Could not read data from


