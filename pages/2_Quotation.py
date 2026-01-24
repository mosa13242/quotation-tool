import streamlit as st
import pandas as pd
from thefuzz import process
import os

st.set_page_config(layout="wide")

st.title("💰 نظام التسعير والبحث الذكي")

# --------------------------------------------------
# LOAD MASTER
# --------------------------------------------------

MASTER_FILE = "master_list.xlsx"

@st.cache_data
def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame()
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df

master_df = load_master()

if master_df.empty:
    st.error("❌ الماستر ليست غير موجود")
    st.stop()

# --------------------------------------------------
# MASTER COLUMN SELECT
# --------------------------------------------------

st.subheader("⚙️ إعدادات الماستر ليست")

col1, col2 = st.columns(2)

with col1:
    master_item_col = st.selectbox(
        "📦 عمود الأصناف في الماستر:",
        master_df.columns,
        key="master_item_col"
    )

with col2:
    master_price_col = st.selectbox(
        "💰 عمود السعر في الماستر:",
        master_df.columns,
        key="master_price_col"
    )

# --------------------------------------------------
# UPLOAD RFQ FILE
# --------------------------------------------------

st.divider()
st.subheader("📤 ارفع ملف العميل")

uploaded = st.file_uploader(
    "ارفع Excel",
    type=["xlsx"]
)

if not uploaded:
    st.stop()

rfq_df = pd.read_excel(uploaded)
rfq_df.columns = [c.strip() for c in rfq_df.columns]

st.success("✅ تم رفع الملف")

# --------------------------------------------------
# RFQ COLUMN SELECT
# --------------------------------------------------

st.subheader("📑 أعمدة ملف العميل")

c1, c2 = st.columns(2)

with c1:
    rfq_item_col = st.selectbox(
        "📦 عمود الصنف:",
        rfq_df.columns
    )

with c2:
    rfq_qty_col = st.selectbox(
        "🔢 عمود الكمية:",
        rfq_df.columns
    )

# --------------------------------------------------
# MATCH BUTTON
# --------------------------------------------------

if st.button("🔍 تنفيذ المطابقة الذكية"):

    results = []

    master_items = master_df[master_item_col].astype(str).tolist()

    for _, row in rfq_df.iterrows():

        item = str(row[rfq_item_col])

        match, score = process.extractOne(item, master_items)

        price_row = master_df.loc[
            master_df[master_item_col] == match,
            master_price_col
        ]

        if not price_row.empty:
            price = float(price_row.values[0])
        else:
            price = 0

        results.append({
            "الصنف المطلوب": item,
            "الصنف المطابق": match,
            "درجة التطابق": score,
            "الكمية": row[rfq_qty_col],
            "السعر": price
        })

    result_df = pd.DataFrame(results)

    st.success("✅ تمت المطابقة")

    st.dataframe(result_df, use_container_width=True)

    # DOWNLOAD
    st.download_button(
        "⬇️ تحميل النتيجة",
        result_df.to_excel(index=False),
        file_name="quotation_result.xlsx"
    )
