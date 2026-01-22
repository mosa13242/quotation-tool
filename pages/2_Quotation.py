import streamlit as st
import pandas as pd
import io

# =============================
# Page Config
# =============================
st.set_page_config(page_title="Quotation Tool", layout="wide")
st.title("Quotation Tool")
st.write("Upload Excel or PDF file (Item + Quantity) to generate quotation")

# =============================
# Load Master List (Excel)
# =============================
try:
    master_df = pd.read_excel("master_list.xlsx")
except Exception as e:
    st.error("Master list file not found: master_list.xlsx")
    st.stop()

master_df.columns = master_df.columns.map(lambda x: str(x).strip())

# =============================
# Upload File
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
                st.error("pdfplumber not installed")
                st.stop()

            tables = []
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        tables.extend(table)

            if len(tables) < 2:
                st.error("No readable table found in PDF")
                st.stop()

            quote_df = pd.DataFrame(tables[1:], columns=tables[0])

        else:
            st.error("Unsupported file type")
            st.stop()

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # =============================
    # Clean Columns
    # =============================
    quote_df.columns = quote_df.columns.map(lambda x: str(x).strip())

    if "Item" not in quote_df.columns or "Quantity" not in quote_df.columns:
        if quote_df.shape[1] >= 2:
            quote_df = quote_df.iloc[:, :2]
            quote_df.columns = ["Item", "Quantity"]
        else:
            st.error("File must contain Item and Quantity")
            st.stop()

    quote_df["Item"] = quote_df["Item"].astype(str).str.strip()
    quote_df["Quantity"] = pd.to_numeric(quote_df["Quantity"], errors="coerce").fillna(0)

    # =============================
    # Merge
    # =============================
    result = quote_df.merge(master_df, on="Item", how="left")

    result["Unit_Price"] = pd.to_numeric(result["Unit_Price"], errors="coerce").fillna(0)
    result["VAT_Percent"] = pd.to_numeric(result["VAT_Percent"], errors="coerce").fillna(0)

    # =============================
    # Calculations
    # =============================
    result["Total_Before_VAT"] = result["Quantity"] * result["Unit_Price"]
    result["VAT_Value"] = result["Total_Before_VAT"] * (result["VAT_Percent"] / 100)
    result["Total_After_VAT"] = result["Total_Before_VAT"] + result["VAT_Value"]

    # =============================
    # Display
    # =============================
    st.subheader("Quotation Result")
    st.dataframe(result, use_container_width=True)

    st.subheader("Totals")
    col1, col2 = st.columns(2)
    col1.metric("Total Before VAT", f"{result['Total_Before_VAT'].sum():,.2f}")
    col2.metric("Total After VAT", f"{result['Total_After_VAT'].sum():,.2f}")

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
