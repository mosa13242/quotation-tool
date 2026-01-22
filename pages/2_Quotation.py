import streamlit as st
import pandas as pd
import difflib  # مكتبة للمقارنة التقريبية للنصوص

st.set_page_config(page_title="Quotation Tool", layout="wide")

st.title("Quotation Tool")
st.write("Upload Excel or PDF file (Item + Quantity)")

uploaded_file = st.file_uploader("Upload Quotation File", type=["xlsx", "pdf"])

def find_best_match(target, columns):
    """دالة للبحث عن أقرب اسم عمود موجود في الملف"""
    # تحويل الكل لحروف صغيرة لتسهيل البحث
    columns_lower = [c.lower() for c in columns]
    target_lower = target.lower()
    
    # البحث عن تطابق مباشر أولاً
    if target_lower in columns_lower:
        return columns[columns_lower.index(target_lower)]
    
    # إذا لم يوجد تطابق مباشر، نبحث عن أقرب كلمة (مثل Unit بدلاً من Unit_Price)
    matches = difflib.get_close_matches(target_lower, columns_lower, n=1, cutoff=0.3)
    if matches:
        return columns[columns_lower.index(matches[0])]
    
    # بحث إضافي إذا كانت الكلمة الهدف جزء من اسم العمود (مثل 'Price' موجودة في 'Unit Price')
    for col in columns:
        if target_lower in col.lower() or col.lower() in target_lower:
            return col
    return None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.astype(str).str.strip() # تنظيف الأسماء
            
            # تحديد الأعمدة المطلوبة بالبحث التقريبي
            col_quantity = find_best_match("Quantity", df.columns)
            col_unit_price = find_best_match("Unit Price", df.columns)
            
            if col_quantity and col_unit_price:
                st.success(f"تم الربط تلقائياً: الكمية ({col_quantity})، السعر ({col_unit_price})")
                
                # تحويل البيانات لأرقام لضمان الحساب الصحيح
                df[col_quantity] = pd.to_numeric(df[col_quantity], errors='coerce').fillna(0)
                df[col_unit_price] = pd.to_numeric(df[col_unit_price], errors='coerce').fillna(0)
                
                # إجراء العملية الحسابية
                df["Subtotal"] = df[col_quantity] * df[col_unit_price]
                
                st.dataframe(df)
            else:
                st.error("لم أتمكن من العثور على أعمدة الكمية أو السعر بشكل تلقائي.")
                st.info(f"الأعمدة المكتشفة في ملفك هي: {list(df.columns)}")

        elif uploaded_file.name.endswith('.pdf'):
            st.info("جاري العمل على دعم ملفات PDF...")

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
else:
    st.info("يرجى رفع ملف إكسل للبدء.")
