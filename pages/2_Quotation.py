import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Quotation", layout="wide")
st.title("Quotation")

# الاتصال بقاعدة البيانات
conn = sqlite3.connect("data.db", check_same_thread=False)

# تحميل Master List
master_df = pd.read_sql("SELECT * FROM master_items", conn)

# رفع ملف التسعير
uploaded_file = st.file_uploader(
    "Upload Quotation Excel (Item + Quantity فقط)",
    type=["xlsx"]
)

if uploaded_file:
    quote_df = pd.read_excel(uploaded_file)

    required_cols = {"Item", "Quantity"}
    if not required_cols.issubset(quote_df.columns):
        st.error("Excel لازم يحتوي على عمودين فقط: Item و Quantity")
        st.stop()

    # دمج مع Master List
    merged = quote_df.merge(
        master_df,
        on="Item",
        how="left",
        indicator=True
    )

    # أصناف مش موجودة
    missing_items = merged[merged["_merge"] == "left_only"]["Item"].tolist()

    if missing_items:
        st.warning("الأصناف دي مش موجودة في Master List:")
        st.write(missing_items)

    # حذف اللي مش موجود
    merged = merged[merged["_merge"] == "both"]

    # تحويل أرقام
    merged["Quantity"] = pd.to_numeric(merged["Quantity"], errors="coerce").fillna(0)
    merged["Unit_Price"] = pd.to_numeric(merged["Unit_Price"], errors="coerce").fillna(0)
    merged["VAT_Percent"] = pd.to_numeric(merged["VAT_Percent"], errors="coerce").fillna(0)

    # حسابات
    merged["Total_Before_VAT"] = merged["Quantity"] * merged["Unit_Price"]
    merged["VAT_Amount"] = merged["Total_Before_VAT"] * merged["VAT_Percent"] / 100
    merged["Total_After_VAT"] = merged["Total_Before_VAT"] + merged["VAT_Amount"]

    # ترتيب الأعمدة
    final_df = merged[
        [
            "Item",
            "Quantity",
            "Unit",
            "Unit_Price",
            "VAT_Percent",
            "Total_Before_VAT",
            "VAT_Amount",
            "Total_After_VAT",
        ]
    ]

    st.subheader("Quotation Result")
    st.dataframe(final_df, use_container_width=True)

    st.subheader("Grand Totals")
    st.success(f"Total Before VAT: {final_df['Total_Before_VAT'].sum():,.2f}")
    st.success(f"VAT: {final_df['VAT_Amount'].sum():,.2f}")
    st.success(f"Total After VAT: {final_df['Total_After_VAT'].sum():,.2f}")
