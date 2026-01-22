import streamlit as st
import pandas as pd
import difflib

st.set_page_config(page_title="Quotation Tool", layout="wide")

st.title("Quotation Tool 2.0")

uploaded_file = st.file_uploader("Upload Quotation File", type=["xlsx"])

def find_best_columns(columns):
    """تخمين أعمدة الكمية والسعر من القائمة"""
    col_map = {"qty": None, "price": None}
    
    # كلمات دالة للبحث عنها
    qty_keywords = ['quantity', 'qty', 'الكمية', 'العدد', 'count']
    price_keywords = ['price', 'unit price', 'rate', 'cost', 'السعر', 'سعر الوحدة', 'unit_price']

    for col in columns:
        c_low = str(col).lower().strip()
        # فحص الكمية
        if any(k in c_low for k in qty_keywords) and not col_map["qty"]:
            col_map["qty"] = col
        # فحص السعر (نتجنب كلمة Unit إذا كانت تعني وحدة القياس مثل Box/Pcs)
        if any(k in c_low for k in price_keywords) and not col_map["price"]:
            col_map["price"] = col
            
    return col_map

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.astype(str).str.strip()
        
        # تخمين الأعمدة
        matches = find_best_columns(df.columns)
        
        st.subheader("إعدادات الأعمدة")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_qty = st.selectbox("اختر عمود الكمية:", df.columns, 
                                        index=list(df.columns).index(matches["qty"]) if matches["qty"] else 0)
        with col2:
            # هنا يمكنك اختيار العمود الذي يحتوي على "السعر" فعلياً إذا كان 'Unit' خطأ
            selected_price = st.selectbox("اختر عمود السعر:", df.columns, 
                                          index=list(df.columns).index(matches["price"]) if matches["price"] else 0)

        if st.button("تحديث الحسابات"):
            # تحويل للرقميات مع معالجة القيم الفارغة
            df[selected_qty] = pd.to_numeric(df[selected_qty], errors='coerce').fillna(0)
            df[selected_price] = pd.to_numeric(df[selected_price], errors='coerce').fillna(0)
            
            # الحساب
            df["Subtotal"] = df[selected_qty] * df[selected_price]
            
            st.success(f"تم الحساب بناءً على: الكمية ({selected_qty}) والسعر ({selected_price})")
            st.dataframe(df.style.format({"Subtotal": "{:.2f}", selected_price: "{:.2f}"}))
            
            # إجمالي الفاتورة النهائي
            total_sum = df["Subtotal"].sum()
            st.metric("إجمالي الفاتورة", f"{total_sum:,.2f}")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
