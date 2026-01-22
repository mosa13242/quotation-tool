import streamlit as st
import pandas as pd
import io

st.title("📋 إدارة وتحميل الماستر لست")

try:
    # تحميل البيانات الحالية
    df_master = pd.read_excel("master_list.xlsx")
    
    # محرر البيانات التفاعلي
    edited_df = st.data_editor(df_master, num_rows="dynamic", use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 حفظ التعديلات"):
            edited_df.to_excel("master_list.xlsx", index=False)
            st.success("تم الحفظ بنجاح!")
            
    with col2:
        # وظيفة تحميل الملف كـ Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(
            label="📥 تحميل الماستر كملف Excel",
            data=buffer.getvalue(),
            file_name="master_list_backup.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
except Exception as e:
    st.error("خطأ: لم يتم العثور على ملف الماستر أو الملف تالف.")
