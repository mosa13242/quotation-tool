import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quotation Tool", layout="wide")

st.title("Quotation Tool")
st.write("Upload Excel or PDF file (Item + Quantity)")

# تحميل الملف
uploaded_file = st.file_uploader("Upload Quotation File", type=["xlsx", "pdf"])

if uploaded_file is not None:
    try:
        # قراءة ملف الإكسل
        if uploaded_file.name.endswith('.xlsx'):
            quote_df = pd.read_excel(uploaded_file)
            
            # 1. تنظيف أسماء الأعمدة (إزالة المسافات الزائدة وتحويلها لنص موحد)
            quote_df.columns = quote_df.columns.str.strip()
            
            # 2. عرض الأعمدة الموجودة للتأكد (اختياري - يمكنك حذفه لاحقاً)
            st.write("Columns found in file:", list(quote_df.columns))
            
            # 3. التحقق من وجود الأعمدة المطلوبة قبل الحساب
            required_cols = ["Quantity", "Unit_Price"]
            
            # فحص إذا كانت الأعمدة موجودة (حتى لو كانت بحروف صغيرة)
            # سنقوم بتحويل أسماء الأعمدة كلها لحروف كبيرة لتسهيل المقارنة
            col_map = {col.lower(): col for col in quote_df.columns}
            
            if "quantity" in col_map and "unit_price" in col_map:
                q_col = col_map["quantity"]
                p_col = col_map["unit_price"]
                
                # إجراء العملية الحسابية
                quote_df["Subtotal"] = quote_df[q_col] * quote_df[p_col]
                
                st.success("Calculation successful!")
                st.dataframe(quote_df)
            else:
                st.error(f"Missing columns! Make sure the file has: {required_cols}")
                st.info(f"Available columns are: {list(quote_df.columns)}")

        elif uploaded_file.name.endswith('.pdf'):
            st.info("PDF processing logic goes here...")

    except Exception as e:
        st.error(f"An error occurred: {e}")

else:
    st.info("Please upload an Excel file to start.")
