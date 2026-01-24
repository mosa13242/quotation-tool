import streamlit as st
import pandas as pd
from thefuzz import process
import os
from io import BytesIO

st.set_page_config(layout="wide")

st.title("💰 نظام التسعير والبحث الذكي")

MASTER_FILE = "master_list.xlsx"

# -------------------------------
# LOAD MASTER
# -------------------------------

@st.cache_data
def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame()
    df = pd.read_excel(MASTER_FILE)
    df.columns = df.columns.str.strip()
    return df

master_df = load_master()

if master_df.empty:
    st.error("❌ الماستر ليست غير موجود")
    st.stop()

# -------------------------------
# SELECT MASTER COLS
# -------------------------------

st.subheader("⚙️ إعدادات الماستر")

c1, c2 = st.columns(2)

with c1:
    master_item_col = st.selectbox(
        "📦 عمود الصنف",
        master_df.columns
    )

with c2:
    master_price_col = st.selectbox(
        "💰 عمود السعر",
        master_df.columns
    )

# -------------------------------
# UPLOAD RFQ
# -------------------------------

st.divider()
st.subheader("📤 ملف العميل")

uploaded = st.file_uploader(
    "ارفع ملف Excel",
    type=["xlsx"]
)

if not uploaded:
    st.stop()

rfq_df = pd.read_excel(uploaded)
rfq_df.columns = rfq_df.columns.str.strip()

# -------------------------------
# RFQ COLS
# -------------------------------

st.subheader("📑 أعمدة ملف العميل")

c1, c2 = st.columns(2)

with c1:
    rfq_item_col = st.selectbox(
        "📦 عمود الصنف",
        rfq_df.columns
    )

with c2:
    rfq_qty_col = st.selectbox(
        "🔢 عمود الكمية",
        rfq_df.columns
    )

# -------------------------------
# MATCH BUTTON
# -------------------------------

if st.button("🔍 تنفيذ المطابقة"):

    results = []

    master_items = master_df[master_item_col].astype(str).tolist()

    for _, row in rfq_df.iterrows():

        item = str(row[rfq_item_col])

        match, score = process.extractOne(item, master_items)

        price_row = master_df.loc[
            master_df[master_item_col] == match,
            master_price_col
        ]

        price = float(price_row.values[0]) if not price_row.empty else 0

        results.append({
            "Requested Item": item,
            "Matched Item": match,
            "Match Score": score,
            "Quantity": row[rfq_qty_col],
            "Price": price,
            "Remarks": "",
            "Confirmed": False
        })

    st.session_state["quotation_df"] = pd.DataFrame(results)

# -------------------------------
# SHOW + EDIT
# -------------------------------

if "quotation_df" in st.session_state:

    st.subheader("📊 نتائج المطابقة")

    edited_df = st.data_editor(
        st.session_state["quotation_df"],
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Confirmed": st.column_config.CheckboxColumn("Confirm Match"),
            "Remarks": st.column_config.TextColumn("Remarks")
        }
    )

    st.session_state["quotation_df"] = edited_df

    # -------------------------------
    # DOWNLOAD
    # -------------------------------

    buffer = BytesIO()
    edited_df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "⬇️ تحميل النتيجة",
        data=buffer,
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
