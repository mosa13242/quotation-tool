import streamlit as st
import pandas as pd
import sqlite3
import io
import pdfplumber

# -----------------------
# Database
# -----------------------
DB_NAME = "data.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS master_list (
            Item TEXT,
            Unit TEXT,
            Unit_Price REAL,
            VAT_Percent REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

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

def load_master():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM master_list", conn)
    conn.close()
    return df

# -----------------------
# UI
# -----------------------
st.set_page_config(page_title="Quotation Tool", layout="wide")

menu = st.sidebar.radio("Menu", ["Master List", "Quotation"])

# =======================
# MASTER LIST PAGE
# =======================
if menu == "Master List":
    st.title("Master List")

    file = st.file_uploader("Upload Master List Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)

        df.columns = df.columns.str.strip()

        required = {"Item", "Unit", "Unit_Price", "VAT_Percent"}
        if not required.issubset(df.columns):
            st.error("Excel must contain: Item, Unit, Unit_Price, VAT_Percent")
        else:
            st.dataframe(df)

            if st.button("Save Master List"):
                conn = get_conn()
                conn.execute("DELETE FROM master_list")
                df.to_sql("master_list", conn, if_exists="append", index=False)
                conn.commit()
                conn.close()
                st.success("Master List saved successfully ✅")

# =======================
# QUOTATION PAGE
# =======================
if menu == "Quotation":
    st.title("Quotation Tool")
    st.write("Upload Excel or PDF (Item + Quantity)")

    try:
        master_df = load_master()
        if master_df.empty:
            st.warning("Master List is empty. Upload it first.")
            st.stop()
    except:
        st.error("Cannot load Master List")
        st.stop()

    file = st.file_uploader("Upload Excel or PDF", type=["xlsx", "pdf"])

    if file:
        if file.name.endswith(".xlsx"):
            order_df = pd.read_excel(file)
        else:
            order_df = read_pdf_items(file)

        order_df.columns = order_df.columns.str.strip()

        if not {"Item", "Quantity"}.issubset(order_df.columns):
            st.error("File must contain Item & Quantity")
            st.stop()

        # Merge with master
        result = order_df.merge(master_df, on="Item", how="left")

        result["Quantity"] = result["Quantity"].fillna(1)
        result["Unit_Price"] = result["Unit_Price"].fillna(0)
        result["VAT_Percent"] = result["VAT_Percent"].fillna(0)

        result["SubTotal"] = result["Quantity"] * result["Unit_Price"]
        result["VAT"] = result["SubTotal"] * (result["VAT_Percent"] / 100)
        result["Total"] = result["SubTotal"] + result["VAT"]

        st.subheader("Quotation Preview")
        st.dataframe(result)

        st.subheader("Grand Total")
        st.success(f"{result['Total'].sum():.2f}")

        # Export Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result.to_excel(writer, index=False, sheet_name="Quotation")

        st.download_button(
            "Download Quotation Excel",
            data=output.getvalue(),
            file_name="quotation.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )



