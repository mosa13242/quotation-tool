import streamlit as st
import pandas as pd
import os

MASTER_FILE = "master_list.xlsx"

st.set_page_config(page_title="Quotation", layout="wide")

# -----------------------------
# Load master list
# -----------------------------

def load_master_safe():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["item", "price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []

    df = pd.read_excel(MASTER_FILE)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df, df["item"].astype(str).tolist()


master_df, master_items = load_master_safe()

st.title("🧾 Quotation Generator")

# -----------------------------
# Check columns
# -----------------------------

required_cols = ["item", "price"]

missing = [c for c in required_cols if c not in master_df.columns]

if missing:
    st.error(f"❌ الأعمدة التالية غير موجودة في master_list.xlsx: {missing}")
    st.write("📌 الأعمدة الموجودة:")
    st.write(master_df.columns.tolist())
    st.stop()

# -----------------------------
# Upload RFQ
# -----------------------------

rfq_file = st.file_uploader("📤 Upload RFQ Excel", type=["xlsx"])

if rfq_file:

    rfq_df = pd.read_excel(rfq_file)

    rfq_df.columns = (
        rfq_df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    st.subheader("RFQ Preview")
    st.dataframe(rfq_df)

    item_col = st.selectbox("📦 اختر عمود الصنف", rfq_df.columns)
    qty_col = st.selectbox("📊 اختر عمود الكمية", rfq_df.columns)

    if st.button("🚀 Generate Quotation"):

        price_map = dict(
            zip(master_df["item"].astype(str), master_df["price"])
        )

        rfq_df["item_clean"] = rfq_df[item_col].astype(str)

        rfq_df["price"] = rfq_df["item_clean"].map(price_map)

        missing_items = rfq_df[rfq_df["price"].isna()]

        if not missing_items.empty:
            st.warning("⚠ أصناف غير موجودة في الماستر ليست:")
            st.dataframe(missing_items[[item_col]])
            st.stop()

        rfq_df["quantity"] = rfq_df[qty_col]
        rfq_df["total"] = rfq_df["quantity"] * rfq_df["price"]

        st.success("✅ Quotation Generated")

        result = rfq_df[[item_col, "quantity", "price", "total"]]

        st.dataframe(result)

        st.download_button(
            "⬇ Download Quotation Excel",
            result.to_excel(index=False),
            file_name="quotation.xlsx"
        )

