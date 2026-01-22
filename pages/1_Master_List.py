import streamlit as st
import pandas as pd
import os
import io

st.title("📋 إدارة وتحميل الماستر لست")

MASTER_FILE = "master_list.xlsx"

if os.path.exists(MASTER_FILE):
    # تحميل البيانات
    df_master = pd.read_excel(MASTER_FILE)
    
    st.subheader("تعديل أصناف الماستر:")
    # جدول تعديل ديناميكي
    edited_df = st.data_editor(df_master, num_rows="dynamic", use_container_width=True, key="master_editor")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 حفظ التعديلات"):
            edited_df.to_excel(MASTER_FILE, index=False)
            st.success("تم الحفظ!")
            
    with col2:
        # زر لتحميل الملف للتأكد من وجوده على جهازك
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 تحميل ملف master_list.xlsx",
            data=buffer.getvalue(),
            file_name="master_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.error("❌ ملف الماستر غير موجود، ارجع للصفحة الرئيسية لإنشائه.")
