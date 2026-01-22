import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Quotation", layout="wide")
st.title("Quotation")

# =========================
# Database connection
# =========================
conn = sqlite3.connect("quotation.db", check_same_thread=False)

# =========================
# Upload quotation excel
# =========================
uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity فقط)",
    type=["xlsx"]
)

if uploaded_file:
    # =========================
    # Read Excel
    # =========================
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # =========================
    # Detect columns automatically
    # =========================
    cols_lower = {c.lower(): c for c in df.columns}

    # Item column
    if "item" in cols_lower:
        item_col = cols_lower["item"]
    elif "product" in cols_lower:
        item_col = cols_lower["product"]
    else:
        st.error("Excel must contain column: Item")
        st.stop()

    # Quantity column
    if "quantity" in cols_lower:
        qty_col = cols_lower["quantity"]
    elif "qty" in cols_lower:
        qty_col = cols_lower["qty"]
    else:
        st.error("Excel must contain column: Quantity or Qty")
        st.stop()

    df = df.rename(columns={
        item_col: "Item",
        qty_col: "Quantity"
    })

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)

    # =========================
    # Load master list
    # =========================
    master_df = pd.read_sql(
        "SELECT Item, Unit, Unit_Price, VAT_Percent FROM master_items",
        conn
    )

    # =========================
    # Merge
    # =========================
    merged = df.merge(master_df, on="Item", how="left")

    # =========================
    # Calculations
    # =========================
    merged["Unit_Price"] = pd.to_numeric(merged["Unit_Price"], errors="coerce").fillna(0)
    merged["VAT_Percent"] = pd.to_numeric(merged["VAT_Percent"], errors="coerce").fillna(0)

    merged["Total_Before_VAT"] = merged["Quantity"] * merged["Unit_Price"]
    merged["VAT_Amount"] = merged["Total_Before_VAT"] * (merged["VAT_Percent"] / 100)
    merged["Total_After_VAT"] = merged["Total_Before_VAT"] + merged["VAT_Amount"]

    # =========================
    # Display result
    # =========================
    st.subheader("Quotation Result")
    st.dataframe(merged, use_container_width=True)

    # =========================
    # Summary
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Before VAT",
        f"{merged['Total_Before_VAT'].sum():,.2f}"
    )
    col2.metric(
        "VAT Amount",
        f"{merged['VAT_Amount'].sum():,.2f}"
    )
    col3.metric(
        "Grand Total",
        f"{merged['Total_After_VAT'].sum():,.2f}"
    )

    # =========================
    # Download Excel
    # =========================
   from io import BytesIO

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    output.to_excel(writer, index=False, sheet_name="Quotation")

st.download_button(
    label="Download Quotation Excel",
    data=buffer.getvalue(),
    file_name="Quotation.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

    )

