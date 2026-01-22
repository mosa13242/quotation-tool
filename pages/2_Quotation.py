import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="نظام التسعير السريع", layout="wide")

# 1. تحميل الماستر ليست
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار (master_list.xlsx) غير موجود. يرجى رفعه أولاً.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
# تنظيف أسماء أعمدة الماستر من أي مسافات
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("💰 نظام التسعير السريع (إصدار الإكسل المضمون)")

# 2. رفع طلب العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    # تنظيف أسماء أعمدة ملف العميل فور رفعه
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    st.subheader("⚙️ إعدادات الربط")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("من ملفك الحالي")
        c_item = st.selectbox("عمود اسم الصنف:", df_client.columns)
        c_qty = st.selectbox("عمود الكمية:", df_client.columns)
        
    with col2:
        st.info("من قائمة الأسعار")
        m_item = st.selectbox("عمود الصنف في الماستر:", master_df.columns)
        m_price = st.selectbox("عمود السعر في الماستر:", master_df.columns)

    if st.button("🚀 تنفيذ التسعير"):
        # تنظيف البيانات لضمان نجاح المطابقة
        df_client[c_item] = df_client[c_item].astype(str).str.strip().str.upper()
        master_df[m_item] = master_df[m_item].astype(str).str.strip().str.upper()
        
        # --- الطريقة المضمونة: Mapping ---
        # ننشئ قاموس للأسعار بناءً على الأسماء التي اخترتها أنت
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        
        # جلب السعر بناءً على اسم الصنف
        df_client['Unit_Price_Found'] = df_client[c_item].map(price_map).fillna(0)
        
        # تحويل الأعمدة لأرقام وحساب الإجمالي
        df_client[c_qty] = pd.to_numeric(df_client[c_qty], errors='coerce').fillna(0)
        df_client['Unit_Price_Found'] = pd.to_numeric(df_client['Unit_Price_Found'], errors='coerce').fillna(0)
        df_client["Total"] = df_client[c_qty] * df_client['Unit_Price_Found']
        
        # عرض النتائج
        st.success("✅ تم التسعير!")
        st.dataframe(df_client, use_container_width=True)
        
        # عرض الإجمالي النهائي
        final_total = df_client["Total"].sum()
        st.metric("إجمالي عرض السعر", f"{final_total:,.2f} EGP")
