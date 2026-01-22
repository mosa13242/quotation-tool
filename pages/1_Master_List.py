import streamlit as st
import pandas as pd

st.title("📋 إدارة قائمة الأسعار (Master List)")

try:
    df = pd.read_excel("master_list.xlsx")
    
    st.write("يمكنك تعديل الأسعار أو إضافة أصناف هنا مباشرة:")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="master_editor")
    
    if st.button("💾 حفظ التعديلات في الماستر"):
        edited_df.to_excel("master_list.xlsx", index=False)
        st.success("تم تحديث قائمة الماستر بنجاح!")
except Exception as e:
    st.error("تأكد من وجود ملف master_list.xlsx")
