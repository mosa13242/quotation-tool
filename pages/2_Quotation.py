import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الاحترافي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر بأمان
def load_master_safe():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).tolist()
    return df, names

master_df, master_names = load_master_safe()

st.title("🛡️ نظام التسعير (مسح، إضافة، وحفظ تلقائي)")

# 1. رفع ملف طلب العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (طلب العميل):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلب العميل):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns if not master_df.empty else ["Price"])

    # 2. البحث والمطابقة الأولية
    if st.button("🔍 تنفيذ البحث الذكي"):
        def initial_search(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(initial_search)
        p_lookup = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(p_lookup).fillna(0.0)
        st.session_state['quotation_data'] = df_client

    # 3. جدول التعديل الحر والحفظ التلقائي
    if 'quotation_data' in st.session_state:
        st.warning("💡 ميزة جديدة: امسح النص في REMARKS واكتب صنفاً جديداً خالصاً، ثم ضع سعره لحفظه.")
        
        # استخدام TextColumn لتوفير حرية المسح والكتابة
        edited_df = st.data_editor(
            st.session_state['quotation_data'],
