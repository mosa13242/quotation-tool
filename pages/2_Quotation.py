import streamlit as st
import pandas as pd
import difflib
import os

st.set_page_config(page_title="Auto Pricing Tool", layout="wide")
st.title("💰 نظام التسعير التلقائي")

MASTER_FILE = "master_list.xlsx"

# 1. تحميل الماستر ليست
if os.path.exists(MASTER_FILE):
    master_df = pd.read_excel(MASTER_FILE)
    master_df.columns = master_df.columns.astype(str).str.strip()
    st.sidebar.success("✅ قائمة الأسعار محملة")
else:
    st.error("❌ ملف master_list.xlsx غير موجود. ارفعه أولاً من صفحة Master List.")
    st.stop()

# 2. رفع ملف العميل
uploaded_file = st.file_uploader("ارفع ملف العميل (Excel حالياً)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = df_client.columns.astype(str).str.strip()

    st.subheader("⚙️ إعدادات المطابقة")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        client_item_col = st.selectbox("عمود اسم الدواء (عندك):", df_client.columns)
    with col2:
        master_item_col = st.selectbox("عمود اسم الدواء (في الماستر):", master_df.columns)
    with col3:
        master_price_col = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    if st.button("🚀 ابدأ التسعير"):
        # وظيفة البحث الذكي
        def get_best_match(name, choices):
            m = difflib.get_close_matches(str(name), choices, n=1, cutoff=0.5)
            return m[0] if m else None

        master_names = master_df[master_item_col].astype(str).tolist()
        
        with st.spinner('جاري مطابقة الأسماء...'):
            df_client['Matched_Name'] = df_client[client_item_col].apply(lambda x: get_best_match(x, master_names))
            
            # دمج البيانات لجلب الأسعار
            final_df = pd.merge(df_client, master_df[[master_item_col, master_price_col]], 
                                left_on='Matched_Name', right_on=master_item_col, how='left')

            # البحث عن الكمية
            qty_col = next((c for c in df_client.columns if 'qty' in c.lower() or 'quant' in c.lower() or 'الكمية' in c), df_client.columns[0])
            
            # حسابات نهائية
            final_df[qty_col] = pd.to_numeric(final_df[qty_col], errors='coerce').fillna(0)
            final_df[master_price_col] = pd.to_numeric(final_df[master_price_col], errors='coerce').fillna(0)
            final_df["Total"] = final_df[qty_col] * final_df[master_price_col]
            
            st.success("✅ تم التسعير بنجاح!")
            st.dataframe(final_df)
            st.metric("إجمالي الفاتورة", f"{final_df['Total'].sum():,.2f} EGP")
