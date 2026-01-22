import streamlit as st
import pandas as pd
import sqlite3
import io

# =============================
# Page Title
# =============================
st.set_page_config(page_title="Quotation Tool", layout="wide")
st.title("Quotation Tool")
st.write("Upload Excel or PDF file (Item + Quantity) to generate quotation")

# =============================
# Load Master List from SQLite
# =============================
conn = sqlite3.connect("master.db")
master_df = pd.read_sql("SELECT * FROM master_list", conn)
conn.close()

# Clean master columns
master_df.columns = master_df.columns.map(lambda x: str(x).strip())

# =============================
# File Upload
# =============================
uploaded_file = st.file_uploader(
    "Upload Quotation File (Excel or PDF)",
    type=["xlsx", "xls", "pdf"]
)

if uploaded_file:

    # =============================
    # Read File
    # =============================
    try:
        if uploaded_file.name.endswith((".xlsx", ".xls")):
            quote_df = pd.read_excel(uploaded_file)

        elif uploaded_file.name.endswith(".pdf"):
            st.info("Reading PDF file...")

            try:
                import pdfplumber
            except ImportError:
                st.error("pdfplumber not installed. Please add it to requirements.txt")
                st.stop()

            tables = []
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        tables.extend(table)

            if not tables or len(tables) < 2:
                st.error("No readable table found in PDF. Please upload Excel instead.")
                st.stop()

            quote_df = pd.DataFrame(tables[1:], columns=tables[0])

        else:
            st.error("Unsupported file type")
            st.stop()

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # =============================
    # Clean Columns SAFELY
    # =============================
    quote_df.columns = quote_df.columns.map(lambda x: str(x).strip())

    # =============================
    # Fix PDF / Unknown Headers
    # =============================
    if "Item" not in quote_df.columns or "Quantity" not in quote_df.columns:
        if quote_df.shape[1] >= 2:
            quote_df = quote_df.iloc[:, :2]
            quote_df.columns = ["Item", "Quantity"]
        else:
            st.error("File must contain Item and Quantity columns")
            st.stop()

    # =============================
    # Clean Data
    # =============================
    quote_df["Item"] = quote_df["Item"].astype(str).str.strip()
    quote_df["Quantity"] = pd.to_numeric(quote_df["Quantity"], errors="coerce").fillna(0)

    # =============================
    # Merge with Master List
    # =============================
    result = quote_df.merge(master_df, on="Item", how="left")

    # =============================
    # Validate Prices
    # =============================
    result["Unit_Price"] = pd.to_numeric(result["Unit_Price"], errors="coerce").fillna(0)
    result["VAT_Percent"] = pd.to_numeric(result["VAT_Percent"], errors="coerce").fillna(0)

    # =============================
    # Calculations
    # =============================
    result["Total_Before_VAT"] = result["Quantity"] * result["Unit_Price"]
    result["VAT_Value"] = result["Total_Before_VAT"] * (result["VAT_Percent"] / 100)
    result["Total_After_VAT"] = result["Total_Before_VAT"] + result["VAT_Value"]

    # =============================
    # Display Result
    # =============================
    st.subheader("Quotation Result")
    st.dataframe(result, use_container_width=True)

    # =============================
    # Totals
    # =============================
    st.subheader("Totals")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Before VAT", f"{result['Total_Before_VAT'].sum():,.2f}")

    with col2:
        st.metric("Total After VAT", f"{result['Total_After_VAT'].sum():,.2f}")

    # =============================
    # Download
    # =============================
    output = io.BytesIO()
    result.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "Download Quotation Excel",
        data=output,
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
