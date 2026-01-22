import streamlit as st
import pandas as pd
import os

st.title("📋 إدارة الماستر لست")
MASTER_FILE = "master_list.xlsx"

# إنشاء الملف فوراً إذا لم يكن موجوداً
if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=["Item", "Price"]).to_excel(MASTER_FILE, index=False)

try:
    df_master = pd.read_excel(MASTER_FILE)
    st.write("يمكنك إضافة الأصناف والأسعار هنا مباشرة:")
    
    # محرر بسيط بدون تعقيدات
    edited_master = st.data_editor(df_master, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 حفظ الماستر"):
        edited_master.to_excel(MASTER_FILE, index=False)
        st.success("تم حفظ الماستر بنجاح!")
except Exception as e:
    st.error(f"خطأ: {e}")
