import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير العبقري", layout="wide")

# 1. تحميل الماستر ليست
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار غير موجود.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("🛡️ نظام المطابقة الذكية المتقدم (Edit Mode)")

# 2. رفع طلب العميل
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

    if st.button("🔍 تنفيذ مطابقة ذكية عالية الدقة"):
        master_names = master_df[m_item].astype(str).tolist()
        
        def super_smart_match(text):
            text = str(text).upper()
            # استراتيجية البحث عن الكلمات المفتاحية (مثل CANNULA)
            # تعطي أولوية للمطابقة التي تحتوي على الكلمة الأساسية بالكامل
            best_match = None
            highest_score = 0
            
            for m_name in master_names:
                m_name_upper = m_name.upper()
                # إذا كانت الكلمة الأساسية موجودة في الطرفين، ارفع النتيجة جداً
                if any(word in m_name_upper for word in text.split() if len(word) > 3):
                    score = fuzz.token_set_ratio(text, m_name_upper) + 20 # بونص للكلمات المشتركة
                else:
                    score = fuzz.token_set_ratio(text, m_name_upper)
                
                if score > highest_score:
                    highest_score = score
                    best_match = m_name
            
            return best_match if highest_score > 65 else "⚠️ يحتاج اختيار يدوي"

        with st.spinner('
