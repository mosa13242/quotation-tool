import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="إدارة الماستر", layout="wide")
st.title("📋 إدارة وتحميل الماستر لست (Master List)")

# اسم ملف القاعدة
MASTER_FILE = "master_list.xlsx"

# 1. التأكد من وجود الملف أو إنشاؤه فوراً لعدم ظهور خطأ
if not os.path.exists(MASTER_FILE):
    df_init = pd.DataFrame(columns=["Item", "Price"])
    df_init.to_excel(MASTER_FILE, index=False)
    st.info("💡 تم إنشاء ملف ماستر جديد لأنه لم يكن موجوداً.")

try:
    # 2. قراءة البيانات الحالية
    df_master = pd.read_excel(MASTER_FILE)
    
    st.write("أضف الأصناف والأسعار في الجدول أدناه، ثم اضغط حفظ:")
    
    # 3. عرض جدول التعديل (Data Editor) بدون تعقيدات مسببة للخطأ
    edited_df = st.data_editor(
        df_master, 
        num_rows="dynamic", # يسمح لك بإضافة صفوف جديدة بالضغط على +
        use_container_width=True, 
        key="master_table_v10"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # زر الحفظ لتحديث الملف على السيرفر
        if st.button("💾 حفظ التعديلات في الماستر"):
            edited_df.to_excel(MASTER_FILE, index=False)
            st.success("✅ تم حفظ البيانات بنجاح في ملف master_list.xlsx")
            
    with col2:
        # زر التحميل للتأكد من وجود الملف على جهازك
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 تحميل نسخة من الماستر لست (Excel)",
            data=buffer.getvalue(),
            file_name="master_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

except Exception as e:
    st.error(f"⚠️ حدث خطأ أثناء التعامل مع الملف: {e}")
