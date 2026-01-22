import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Master List Management", layout="wide")
st.title("🗂️ إدارة وتحميل قائمة الأسعار (Master List)")

MASTER_FILE = "master_list.xlsx"

# رفع ملف جديد
uploaded_master = st.file_uploader("ارفع ملف الإكسل الذي يحتوي على الأسعار الأصلية", type=["xlsx"])

if uploaded_master:
    df_temp = pd.read_excel(uploaded_master)
    # تنظيف أسماء الأعمدة عند الحفظ
    df_temp.columns = df_temp.columns.astype(str).str.strip()
    df_temp.to_excel(MASTER_FILE, index=False)
    st.success("✅ تم تحديث قائمة الأسعار بنجاح!")

# عرض البيانات الموجودة حالياً
if os.path.exists(MASTER_FILE):
    st.subheader("📋 قائمة الأسعار الحالية")
    current_df = pd.read_excel(MASTER_FILE)
    st.dataframe(current_df, use_container_width=True)
    
    if st.button("🗑️ حذف القائمة الحالية"):
        os.remove(MASTER_FILE)
        st.warning("تم حذف الملف، يرجى رفع ملف جديد.")
        st.rerun()
else:
    st.info("💡 لا يوجد ملف أسعار حالياً. يرجى رفع ملف إكسل ليعمل نظام التسعير.")
