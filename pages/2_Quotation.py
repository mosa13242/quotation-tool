import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="التسعير البسيط", layout="wide")

# 1. تحميل قائمة الأسعار الأساسية (Master List)
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار غير موجود. ارفعه أولاً من صفحة Master List.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
# تنظيف المسافات من أسماء الأعمدة
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("💰 نظام التسعير السريع (Excel فقط)")

# 2. رفع ملف العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    # قراءة ملف العميل
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    st.subheader("⚙️ إعدادات الربط")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("--- من ملفك الحالي ---")
        client_item = st.selectbox("عمود اسم الدواء (عندك):", df_client.columns)
        client_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
        
    with c2:
        st.write("--- من قائمة الأسعار ---")
        master_item = st.selectbox("عمود الاسم (في الماستر):", master_df.columns)
        master_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    if st.button("🚀 تنفيذ التسعير"):
        # تنظيف نصوص الأصناف لضمان التطابق
        df_client[client_item] = df_client[client_item].astype(str).str.strip()
        master_df[master_item] = master_df[master_item].astype(str).str.strip()
        
        # --- حل مشكلة KeyError نهائياً ---
        # بدلاً من عمل Merge، سنستخدم طريقة "القاموس" لجلب السعر
        # هذه الطريقة لا تغير أسماء الأعمدة ولا تسبب أخطاء KeyError
        price_mapping = dict
