import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz  # مكتبة البحث الذكي بالتقريب

st.set_page_config(page_title="نظام التسعير الذكي", layout="wide")

# 1. تحميل قائمة الأسعار (Master List)
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار غير موجود. يرجى رفعه من صفحة Master List.")
    st.stop()

# قراءة الماستر وتجهيزه
master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("🤖 نظام التسعير الذكي (البحث بالتقريب)")

# 2. رفع طلب العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # واجهة اختيار الأعمدة ديناميكياً لتجنب KeyError
    st.subheader("⚙️ إعدادات المطابقة")
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود اسم الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    # منزلق للتحكم في دقة الذكاء (Threshold)
    threshold = st.slider("دقة المطابقة الذكية (80% هي الأفضل):", 50, 100, 80)

    if st.button("🚀 ابدأ التسعير الذكي"):
        with st.spinner('جاري البحث في الماستر ليست ومطابقة الأصناف...'):
            
            # قائمة الأسماء من الماستر للبحث فيها
            master_names = master_df[m_item].astype(str).tolist()
            
            # دالة البحث الذكي
            def get_best_match(name):
                # يبحث عن أقرب اسم صنف في الماستر
                res = process.extractOne(str(name), master_names, scorer=fuzz.token_sort_ratio)
                if res and res[1] >= threshold:
                    return res[0] # يعيد الاسم كما هو في الماستر
                return "غير موجود"

            # تنفيذ المطابقة ووضع النتيجة في REMARKS
            df_client['REMARKS'] = df_client[c_item].apply(get_best_match)
            
            # جلب السعر بناءً على الاسم الموجود في REMARKS (الربط المضمون)
            price_map = dict(zip(master_df[m_item], master_df[m_price]))
            df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0)
            
            # الحسابات المالية نهائية
            df_client[c_qty] = pd.to_numeric(df_client[c_qty], errors='coerce').fillna(0)
            df_client['Unit_Price'] = pd.to_numeric(df_client['Unit_Price'], errors='coerce').fillna(0)
            df_client["Total"] = df_client[c_qty] * df_client['Unit_Price']
            
            st.success("✅ اكتملت المطابقة!")
            
            # عرض النتيجة (سيظهر اسم صنف العميل وبجانبه REMARKS من الماستر)
            st.dataframe(df_client, use_container_width=True)
            
            # عرض الإجمالي
            total_val = df_client["Total"].sum()
            st.metric("إجمالي القيمة التقديرية", f"{total_val:,.2f} EGP")

            # زر تحميل النتيجة
            csv_data = df_client.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل النتيجة كملف Excel (CSV)", csv_data, "Quotation_Results.csv", "text/csv")
