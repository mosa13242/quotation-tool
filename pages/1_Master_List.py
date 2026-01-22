import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="إدارة الماستر", layout="wide")
MASTER_FILE = "master_list.xlsx"

st.title("📋 إدارة قائمة الأصناف الرئيسية (Master List)")

# رفع ملف ماستر جديد
uploaded_master = st.file_uploader("تحديث قائمة الماستر (Excel)", type=["xlsx"])
if uploaded_master:
    df_new = pd.read_excel(uploaded_master)
    df_new.to_excel(MASTER_FILE, index=False)
    st.success("تم تحديث ملف الماستر بنجاح!")

# عرض وتعديل الماستر الحالي
if os.path.exists(MASTER_FILE):
    df_master = pd.read_excel(MASTER_FILE)
    st.subheader("القائمة الحالية")
    edited_master = st.data_editor(df_master, num_rows="dynamic", use_container_width=True)
    
    if st.button("حفظ التعديلات اليدوية"):
        edited_master.to_excel(MASTER_FILE, index=False)
        st.success("تم حفظ التعديلات في الماستر.")
