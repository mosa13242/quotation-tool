import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Master List Management", layout="wide")
st.title("🗂️ إدارة قائمة الأسعار (Master List)")

MASTER_FILE = "master_list.xlsx"

# رفع ملف جديد لتحديث الماستر ليست
uploaded_master = st.file_uploader("ارفع ملف Excel لتحديث قائمة الأسعار الأساسية", type=["xlsx"])

if uploaded_master:
    df_master = pd.read_excel(uploaded_master)
    df_master.to_excel(MASTER_FILE, index=False)
    st.success("✅ تم تحديث قائمة الأسعار بنجاح!")

# عرض القائمة الحالية إذا كانت موجودة
if os.path.exists(MASTER_FILE):
    st.subheader("القائمة الحالية")
    current_master = pd.read_excel(MASTER_FILE)
    st.dataframe(current_master, use_container_width=True)
else:
    st.warning("⚠️ لا توجد قائمة أسعار حالية. يرجى رفع ملف master_list.xlsx")
