import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الذكي", layout="wide")

MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (ربط كامل بالماستر + إضافة جديد)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns)

    if st.button("🔍 تنفيذ مطابقة وتحليل"):
        def smart_match(text):
            if not master_names: return "⚠️ صنف جديد"
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else "⚠️ صنف جديد"

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_dict = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_dict).fillna(0)
        st.session_state['df_edit'] = df_client

    if 'df_edit' in st.session_state:
        st.info("💡 الخيارات في REMARKS تأتي من الماستر؛ وإذا كتبت اسماً جديداً وسعراً سيتم حفظهما
