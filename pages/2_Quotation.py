import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz

st.set_page_config(page_title="نظام التسعير التفاعلي", layout="wide")

# 1. تحميل الماستر ليست
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار (master_list.xlsx) غير موجود.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("🤖 تسعير ذكي + تعديل يدوي مباشر")

# 2. رفع طلب العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # إعدادات اختيار الأعمدة لتجنب KeyError
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns)

    if st.button("🔍 تحليل ومطابقة أولية"):
        master_names = master_df[m_item].astype(str).tolist()
        
        # دالة البحث الذكي (كلمة CANNULA ستطابق Butterfly Cannula)
        def smart_match(name):
            match, score = process.extractOne(str(name), master_names, scorer=fuzz.partial_ratio)
            return match if score > 55 else "تحتاج مراجعة"

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        # حفظ البيانات في جلسة العمل (Session State) للتمكن من تعديلها
        st.session_state['temp_df'] = df_client
        st.session_state['master_data'] = dict(zip(master_df[m_item], master_df[m_price]))

    # --- واجهة التعديل اليدوي (Editable Table) ---
    if 'temp_df' in st.session_state:
        st.subheader("📝 راجع عمود REMARKS واضغط للتعديل (EDIT)")
        
        master_list_options = list(st.session_state['master_data'].keys())
        
        # استخدام محرر البيانات للسماح باختيار الصنف يدوياً
        edited_df = st.data_editor(
            st.session_state['temp_df'],
            column_config={
                "REMARKS": st.column_config.SelectboxColumn(
                    "الصنف المختار (اضغط للتعديل)",
                    help="اختر الصنف الصحيح من الماستر ليست إذا كان البحث التلقائي غير دقيق",
                    options=master_list_options,
                    required=True,
                )
            },
            disabled=[c_item, c_qty], # منع تعديل بيانات العميل الأصلية
            use_container_width=True,
            key="editor"
        )

        # زر نهائي لحساب الأسعار بناءً على الاختيارات اليدوية
        if st.button("🚀 اعتماد الاختيارات وحساب الإجمالي"):
            price_map = st.session_state['master_data']
            
            # تحديث السعر بناءً على الصنف المختار في REMARKS
            edited_df['Unit_Price'] = edited_df['REMARKS'].map(price_map).fillna(0)
            
            # الحسابات المالية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            
            st.success("✅ تم تحديث كافة الأسعار بناءً على اختيارك النهائي!")
            st.dataframe(edited_df, use_container_width=True)
            
            st.metric("الإجمالي الكلي للفاتورة", f"{edited_df['Total'].sum():,.2f} EGP")
            
            # تصدير الملف
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل عرض السعر النهائي", csv, "Final_Quote.csv", "text/csv")
