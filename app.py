import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# =========================
# تحميل / إنشاء الماستر
# =========================
def get_safe_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df["Item"].astype(str).tolist()
    return df, names


# =========================
# واجهة التطبيق
# =========================
st.title("🧾 نظام التسعير")

master_df, master_names = get_safe_master()

# =========================
# رفع طلب العميل
# =========================
st.header("📤 رفع طلب العميل")
uploaded_file = st.file_uploader("ارفع ملف Excel", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]

    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (طلب العميل)", df_client.columns)
        c_qty = st.selectbox("عمود الكمية", df_client.columns)
    with c2:
        m_item = "Item"
        m_price = "Price"

    # =========================
    # المطابقة الذكية
    # =========================
    if st.button("🔍 تنفيذ التسعير"):
        def smart_match(x):
            if not master_names:
                return str(x)
            match, score = process.extractOne(
                str(x), master_names, scorer=fuzz.token_set_ratio
            )
            return match if score >= 70 else str(x)

        df_client["REMARKS"] = df_client[c_item].apply(smart_match)

        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client["Unit_Price"] = df_client["REMARKS"].map(price_map).fillna(0)

        st.session_state.df_work = df_client

# =========================
# التعديل والحفظ
# =========================
if "df_work" in st.session_state:
    st.subheader("✏️ التعديل النهائي")

    edited_df = st.data_editor(
        st.session_state.df_work,
        column_config={
            "REMARKS": st.column_config.TextColumn(
                "الصنف (بحث أو كتابة)",
                suggestions=master_names
            ),
            "Unit_Price": st.column_config.NumberColumn(
                "سعر الوحدة",
                min_value=0.0,
                format="%.2f"
            ),
        },
        disabled=[c_item, c_qty],
        use_container_

