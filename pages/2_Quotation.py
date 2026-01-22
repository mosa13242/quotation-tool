import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz

st.set_page_config(page_title="نظام التسعير الذكي المتطور", layout="wide")

# 1. تحميل الماستر ليست
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار غير موجود. ارفعه من صفحة Master List.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]
master_names = master_df[master_df.columns[0]].astype(str).tolist() # افتراض أول عمود هو الاسم

st.title("🤖 التسعير الذكي مع إمكانية التعديل اليدوي")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # إعدادات الأعمدة
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    if st.button("🔍 تحليل ومطابقة الأصناف"):
        # تنظيف وتحضير البيانات
        master_names = master_df[m_item].astype(str).tolist()
        price_map = dict(zip(master_df[m_item], master_df[m_price]))

        # دالة البحث الجزئي الذكي (لحساب كلمة CANNULA المشتركة)
        def smart_search(name):
            # نستخدم partial_ratio للبحث عن كلمات مشتركة داخل الجملة
            match, score = process.extractOne(str(name), master_names, scorer=fuzz.partial_ratio)
            return match if score > 60 else "تحتاج مراجعة"

        df_client['REMARKS'] = df_client[c_item].apply(smart_search)
        st.session_state['df_result'] = df_client
        st.session_state['price_map'] = price_map

    # --- خيار التعديل اليدوي (Manual Edit) ---
    if 'df_result' in st.session_state:
        st.subheader("📝 مراجعة وتعديل المطابقة")
        st.write("يمكنك تغيير الاختيار في عمود REMARKS إذا لم يكن دقيقاً:")
        
        # استخدام st.data_editor للسماح للمستخدم بالاختيار اليدوي
        edited_df = st.data_editor(
            st.session_state['df_result'],
            column_config={
                "REMARKS": st.column_config.SelectboxColumn(
                    "أقرب صنف في الماستر (EDIT)",
                    help="اختر الصنف الصحيح إذا كان البحث التلقائي غير دقيق",
                    options=master_names,
                    required=True,
                )
            },
            disabled=[c_item, c_qty], # منع تعديل بيانات العميل الأصلية
            hide_index=True,
            use_container_width=True
        )

        if st.button("🚀 اعتماد التسعير النهائي"):
            # جلب الأسعار بناءً على التعديلات اليدوية
            price_map = st.session_state['price_map']
            edited_df['Unit_Price'] = edited_df['REMARKS'].map(price_map).fillna(0)
            
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            
            st.success("✅ تم تحديث الأسعار بناءً على اختياراتك")
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي النهائي", f"{edited_df['Total'].sum():,.2f} EGP")
            
            # تحميل النتيجة
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل ملف التسعير النهائي", csv, "Final_Quotation.csv", "text/csv")
