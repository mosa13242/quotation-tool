import streamlit as st
import pandas as pd
import os

st.title("📋 إدارة الماستر لست")
MASTER_FILE = "master_list.xlsx"

# إنشاء الملف تلقائياً إذا لم يكن موجوداً
if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=["Item", "Price"]).to_excel(MASTER_FILE, index=False)

try:
    df_master = pd.read_excel(MASTER_FILE)
    # محرر بيانات بسيط لتجنب الأخطاء البرمجية
    edited_master = st.data_editor(df_master, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 حفظ الماستر"):
        edited_master.to_excel(MASTER_FILE, index=False)
        st.success("تم الحفظ بنجاح!")
except Exception as e:
    st.error(f"خطأ في تحميل الماستر: {e}")
