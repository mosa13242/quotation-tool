import streamlit as st
import pandas as pd
import difflib

st.set_page_config(page_title="Quotation Tool", layout="wide")

st.title("Quotation Tool 2.0 (Auto-Pricing)")

# 1. تحميل ملف الـ Master List أولاً (يفترض وجوده في مسار معين أو رفعه)
# يمكنك تغيير المسار للملف الفعلي عندك
MASTER_LIST_PATH = "master_list.xlsx" 

try:
    master_df = pd.read_excel(MASTER_LIST_PATH)
    master_df.columns = master_df.columns.astype(str).str.strip()
    st.sidebar.success("✅ تم تحميل قائمة الأسعار (Master List)")
except:
    st.sidebar.error("❌ لم يتم العثور على ملف master_list.xlsx")
    master_df = None

uploaded_file = st.file_uploader("Upload Quotation File", type=["xlsx"])

if uploaded_file and master_df is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.astype(str).str.strip()
        
        st.subheader("إعدادات الربط")
        col1, col2 = st.columns(2)
        
        with col1:
            item_col = st.selectbox("اختر عمود اسم الدواء (في ملفك):", df.columns)
        with col2:
            master_item_col = st.selectbox("اختر عمود اسم الدواء (في Master List):", master_df.columns)
            master_price_col = st.selectbox("اختر عمود السعر (في Master List):", master_df.columns)

        if st.button("بدء التسعير التلقائي"):
            # تنظيف الأسماء لضمان أفضل مطابقة
            df[item_col] = df[item_col].astype(str).str.strip()
            master_df[master_item_col] = master_df[master_item_col].astype(str).str.strip()
            
            # عملية الربط لجلب السعر بناءً على اسم الدواء
            # سيبحث عن السعر في الـ Master List ويضيفه لملفك
            result_df = pd.merge(
                df, 
                master_df[[master_item_col, master_price_col]], 
                left_on=item_col, 
                right_on=master_item_col, 
                how='left'
            )
            
            # تحديد عمود الكمية (نحاول تخمينه)
            qty_col = next((c for c in df.columns if 'quant' in c.lower() or 'qty' in c.lower()), df.columns[0])
            
            # الحسابات
            result_df[qty_col] = pd.to_numeric(result_df[qty_col], errors='coerce').fillna(0)
            result_df[master_price_col] = pd.to_numeric(result_df[master_price_col], errors='coerce').fillna(0)
            
            result_df["Subtotal"] = result_df[qty_col] * result_df[master_price_col]
            
            st.success("تم سحب الأسعار من الـ Master List وحساب الإجمالي!")
            st.dataframe(result_df)
            
            total = result_df["Subtotal"].sum()
            st.metric("إجمالي العرض", f"{total:,.2f}")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
