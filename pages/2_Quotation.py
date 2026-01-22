import streamlit as st
import pandas as pd
import sqlite3
import pdfplumber

# ===============================
# Page Title
# ===============================
st.title("Quotation Tool")

st.write("Upload Excel or PDF file (Item + Quantity) to generate quotation")

# ===============================
# Database Connection
# ===============================
conn = sqlite3.connect("quotation.db", check_same_thread=False)

# ===============================
# Load Master List
# ===============================
try:
    master_df = pd.read_sql("SELECT * FROM master_items", conn)
except Exception as e:
    st.error("Master list not found in database")
    st.stop()

# ===============================
# File Upload (Excel or PDF)
# ===============================
uploaded_file = st.file_uploader(
    "Upload Quotation File (Excel or PDF)",
    type=["xlsx", "pdf"]
)

if uploaded_file is not None:
    file_name = uploaded_file.name.lower()

    # ===============================
    # Read EXCEL
    # ===============================
    if file_name.endswith(".xlsx"):
        quote_df = pd.read_excel(uploaded_file)

    # ===============================
    # Read PDF (text-based)
    # ===============================
    elif file_name.endswith(".pdf"):
        st.info("Reading PDF file...")

        rows = []

        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                for line in text.split("\n"):
                    parts = line.split()
                    if len(parts) >= 2:
                        item = " ".join(parts[:-1])
                        qty = parts[-1]

                        rows.append({
                            "Item": item.strip(),
                            "Quantity": qty
                        })

        quote_df = pd.DataFrame(rows)

    else:
        st.error("Unsupported file type")
        st.stop()

    # ===============================
    # Validate Columns
    # ===============================
    quote_df.columns = quote_df.columns.str.strip()

    if "Item" not in quote_df.columns or "Quantity" not in quote_df.columns:
        st.error("File must contain columns: Item and Quantity")
        st.stop()

    # ===============================
    # Merge with Master List
    # ===============================
    result = quote_df.merge(master_df, on="Item", how="left")

    # ===============================
    # Numeric Conversion
    # ===============================
    result["Quantity"] = pd.to_numeric(result["Quantity"], errors="coerce").fillna(0)
    result["Unit_Price"] = pd.to_numeric(result["Unit_Price"], errors="coerce").fillna(0)
    result["VAT_Percent"] = pd.to_numeric(result["VAT_Percent"], errors="coerce").fillna(0)

    # ===============================
    # Calculations
    # ===============================
    result["Total_Before_VAT"] = result["Quantity"] * result["Unit_Price"]
    result["VAT_Amount"] = result["Total_Before_VAT"] * result["VAT_Percent"] / 100
    result["Total_After_VAT"] = result["Total_Before_VAT"] + result["VAT_Amount"]

    # ===============================
    # Display Result
    # ===============================
    st.subheader("Quotation Result")
    st.dataframe(result)

    # ===============================
    # Totals
    # ===============================
    st.subheader("Totals")
    st.write("Subtotal:", result["Total_Before_VAT"].sum())
    st.write("VAT:", result["VAT_Amount"].sum())
    st.write("Grand Total:", result["Total_After_VAT"].sum())
