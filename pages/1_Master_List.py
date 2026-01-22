import streamlit as st
import pandas as pd

st.title("📋 إدارة الماستر لست (Master List)")

try:
    df_master = pd.read_excel("master_list.xlsx")
    st.write("يمكنك إضافة أصناف أو تعديل أسعار الماستر هنا مباشرة:")
    
    # محرر بيانات تفاعلي
    edited_master = st.data_editor(df_master, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 حفظ التعديلات في الماستر"):
        edited_master.to_excel("master_list.xlsx", index=False)
        st.success("تم تحديث ملف الماستر بنجاح!")
except Exception as e:
    st.error("خطأ في تحميل ملف الماستر. تأكد من وجوده.")


