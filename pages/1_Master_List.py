import streamlit as st
import pandas as pd
import os

st.title("📋 إدارة الماستر لست")

MASTER_FILE = "master_list.xlsx"

# 1. خانة رفع ملف الماستر (لتعبئة القائمة لأول مرة)
st.subheader("📤 رفع قاعدة بيانات جديدة")
uploaded_master = st.file_uploader("ارفع ملف الإكسيل الذي يحتوي على الأصناف والأسعار:", type=["xlsx"], key="master_upload")

if uploaded_master:
    df_new = pd.read_excel(uploaded_master)
    df_new.to_excel(MASTER_FILE, index=False)
    st.success("✅ تم تحديث الماستر لست بنجاح من الملف المرفوع!")

st.markdown("---")

# 2. عرض وتعديل الماستر الحالي
st.subheader("📝 تعديل الأصناف الحالية")
if os.path.exists(MASTER_FILE):
    try:
        df = pd.read_excel(MASTER_FILE)
        # محرر بيانات بسيط ومستقر
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="master_editor_vFinal")
        
        if st.button("💾 حفظ التعديلات اليدوية"):
            edited_df.to_excel(MASTER_FILE, index=False)
            st.success("✅ تم حفظ التعديلات!")
    except Exception as e:
        st.error(f"خطأ في عرض البيانات: {e}")
else:
    st.info("الماستر فارغ حالياً. يمكنك الرفع من الخانة أعلاه أو إضافة صنف يدوياً.")

