import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="إدارة الماستر", layout="wide")
st.title("📋 إدارة وتحميل الماستر لست")

MASTER_FILE = "master_list.xlsx"

# إنشاء الملف فوراً إذا لم يكن موجوداً
if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=["Item", "Price"]).to_excel(MASTER_FILE, index=False)

try:
    df_master = pd.read_excel(MASTER_FILE)
    
    st.write("أضف بياناتك هنا:")
    edited_df = st.data_editor(df_master, num_rows="dynamic", use_container_width=True, key="m_v11")
    
    if st.button("💾 حفظ التعديلات"):
        # محاولة الحفظ بالمحرك الافتراضي لتجنب أخطاء المكتبات
        edited_df.to_excel(MASTER_FILE, index=False)
        st.success("✅ تم الحفظ في ملف master_list.xlsx")
            
    # زر التحميل بصيغة بسيطة
    buffer = io.BytesIO()
    edited_df.to_excel(buffer, index=False)
    st.download_button(
        label="📥 تحميل الماستر (Excel)",
        data=buffer.getvalue(),
        file_name="master_list.xlsx",
        mime="application/vnd.ms-excel"
    )

except Exception as e:
    st.error(f"⚠️ تأكد من إضافة xlsxwriter في ملف requirements.txt. الخطأ الحالي: {e}")
