import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Master List", layout="wide")
st.title("🗂️ إدارة قائمة الأسعار (Master List)")

MASTER_FILE = "master_list.xlsx"

uploaded_master = st.file_uploader("ارفع ملف الإكسل الأساسي للأسعار", type=["xlsx"])

if uploaded_master:
    try:
        df_temp = pd.read_excel(uploaded_master)
        # تنظيف أسماء الأعمدة من أي مسافات مخفية
        df_temp.columns = [str(c).strip() for c in df_temp.columns]
        df_temp.to_excel(MASTER_FILE, index=False)
        st.success("✅ تم تحديث قائمة الأسعار بنجاح!")
    except Exception as e:
        st.error(f"خطأ في حفظ الملف: {e}")

if os.path.exists(MASTER_FILE):
    st.subheader("📋 البيانات المسجلة حالياً")
    st.dataframe(pd.read_excel(MASTER_FILE), use_container_width=True)
