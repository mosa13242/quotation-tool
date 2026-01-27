import streamlit as st
import pandas as pd
import os

MASTER_FILE = "master_list.xlsx"

st.set_page_config(page_title="Quotation", layout="wide")

# -----------------------------
# تحميل الماستر ليست مع تنظيف الأعمدة
# -----------------------------

def load_master_safe():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["item", "unit_price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []

    df = pd.read_excel(MASTER_FILE)

    # تنظيف أسماء الأعمدة
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df, df["item"].astype(str).tolist() if "item" in df.columns else []


master_df, master_items = load_master_safe()

st.title("🧾 Quotation Generator")

# -----------------------------
# تأكيد الأعمدة المطلوبة
# -----------------------------

required_cols = ["item", "unit_price"]

missing = [c for c in required_cols if c not in master_df.columns]

if missing:
    st.error(f"❌ الأعمدة التالية غير موجودة في master_list.xlsx: {missing}")
    st.write("📌 الأعمدة الموجودة:")
    st.write(master_df.columns.tolist())
    st.stop()

# -----------------------------
# رفع ملف RFQ
# -----------------------------

rfq_file = st.file_uploader("📤 Upload RFQ Excel", type=["xlsx"])

if rfq_file:

    rfq_df = pd.read_excel(rfq_file)

    rfq_df.columns = (
        rfq_df.columns
        .astype(str)
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
            zip(master_df["item"].astype(str), master_df["unit_price"])
        )

        rfq_df["item_clean"] = rfq_df[item_col].astype(str)

        rfq_df["unit_price"] = rfq_df["item_clean"].map(price_map)

        missing_items = rfq_df[rfq_df["unit_price"].isna()]

        if not missing_items.empty:
            st.warning("⚠ بعض الأصناف غير موجودة في الماستر ليست:")
            st.dataframe(missing_items[[item_col]])
            st.stop()

        rfq_df["quantity"] = rfq_df[qty_col]
        rfq_df["total"] = rfq_df["quantity"] * rfq_df["unit_price"]

        st.success("✅ Quotation Generated Successfully")

        st.dataframe(
            rfq_df[[item_col, "quantity", "unit_price", "total"]]
        )

        st.download_button(
            "⬇ Download Quotation Excel",
            rfq_df[[item_col, "quantity", "unit_price", "total"]]
            .to_excel(index=False),
            file_name="quotation.xlsx"
        )

