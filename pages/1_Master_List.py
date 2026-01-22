import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="إدارة الأسعار", layout="wide")
st.title("🗂️ إدارة قائمة الأسعار الأساسية (Master List)")

MASTER_FILE = "master_list.xlsx"

# خيار رفع ملف جديد لتحديث البيانات
uploaded_master = st.file_uploader("ارفع ملف Excel الأساسي للأسعار", type=["xlsx"])

if uploaded_master:
    try:
        df_temp = pd.read_excel(uploaded_master)
        # تنظيف أسماء الأعمدة لإزالة المسافات الزائدة
        df_temp.columns = df_temp.columns.astype(str).str.strip()
        df_temp.to_excel(MASTER_FILE, index=False)
        st.success("✅ تم تحديث قائمة الأسعار بنجاح!")
    except Exception as e:
        st.error(f"حدث خطأ أثناء حفظ الملف: {e}")

# عرض القائمة الحالية
if os.path.exists(MASTER_FILE):
    st.subheader("📋 القائمة المسجلة حالياً")
    current_df = pd.read_excel(MASTER_FILE)
    st.dataframe(current_df, use_container_width=True)
else:
    st.info("💡 لا توجد قائمة أسعار حالياً. يرجى رفع ملف أولاً ليعمل نظام التسعير.")
