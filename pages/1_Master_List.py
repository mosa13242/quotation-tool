import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="إدارة الماستر", layout="wide")
st.title("📋 إدارة وتحميل الماستر لست")

MASTER_FILE = "master_list.xlsx"

# إنشاء الملف فوراً إذا لم يكن موجوداً لضمان عدم تعليق الصفحة
if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=["Item", "Price"]).to_excel(MASTER_FILE, index=False)

try:
    # قراءة البيانات مع استثناء الأخطاء
    df_master = pd.read_excel(MASTER_FILE)
    
    st.write("أضف بياناتك هنا (اضغط على + لإضافة صنف جديد):")
    # جدول تعديل مستقر
    edited_df = st.data_editor(df_master, num_rows="dynamic", use_container_width=True, key="master_stable_v12")
    
    if st.button("💾 حفظ التعديلات"):
        edited_df.to_excel(MASTER_FILE, index=False)
        st.success("✅ تم الحفظ بنجاح في ملف master_list.xlsx")
            
    # زر تحميل احتياطي بسيط جداً
    buffer = io.BytesIO()
    edited_df.to_excel(buffer, index=False)
    st.download_button(
        label="📥 تحميل الماستر (Excel)",
        data=buffer.getvalue(),
        file_name="master_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"⚠️ هناك مشكلة في المكتبات البرمجية على السيرفر: {e}")

