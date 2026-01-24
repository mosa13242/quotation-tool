import streamlit as st
import pandas as pd
import os

MASTER_FILE = "master_list.xlsx"

st.title("📋 إدارة الماستر ليست")

uploaded = st.file_uploader(
    "ارفع ملف الماستر ليست (Excel)",
    type=["xlsx"]
)

if uploaded:
    df = pd.read_excel(uploaded)
    df.to_excel(MASTER_FILE, index=False)
    st.success("✅ تم رفع الماستر ليست بنجاح")

# تحميل الحالي لو موجود
if os.path.exists(MASTER_FILE):
    st.subheader("الماستر الحالي")
    df = pd.read_excel(MASTER_FILE)

    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("💾 حفظ التعديلات"):
        edited_df.to_excel(MASTER_FILE, index=False)
        st.success("تم حفظ التعديلات ✔️")
