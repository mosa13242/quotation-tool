import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير العبقري", layout="wide")

# 1. تحميل الماستر ليست
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار غير موجود. ارفعه أولاً من صفحة Master List.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("🛡️ نظام المطابقة الذكية المتقدم (Edit Mode)")

# 2. رفع ملف العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # واجهة اختيار الأعمدة ديناميكياً لتجنب KeyError
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns)

    if st.button("🔍 تنفيذ مطابقة ذكية (تحليل الكلمات)"):
        master_names = master_df[m_item].astype(str).tolist()
        
        def weighted_smart_match(text):
            text = str(text).upper()
            best_match = None
            highest_score = 0
            
            for m_name in master_names:
                m_name_upper = m_name.upper()
                # إذا وجد كلمة كاملة مشتركة (مثل CANNULA)، نعطيه بونص 30 نقطة
                bonus = 30 if any(word in m_name_upper for word in text.split() if len(word) > 3) else 0
                score = fuzz.token_set_ratio(text, m_name_upper) + bonus
                
                if score > highest_score:
                    highest_score = score
                    best_match = m_name
            
            # إذا كانت المطابقة ضعيفة، نتركها للمراجعة اليدوية
            return best_match if highest_score > 60 else "⚠️ يحتاج اختيار يدوي"

        with st.spinner('جاري البحث والمطابقة...'):
            df_client['REMARKS'] = df_client[c_item].apply(weighted_smart_match)
            # تخزين البيانات في الجلسة للسماح بالتعديل التفاعلي
            st.session_state['df_data'] = df_client
            st.session_state['price_dict'] = dict(zip(master_df[m_item], master_df[m_price]))
            st.session_state['m_options'] = master_names

    # --- واجهة الـ EDIT التفاعلية ---
    if 'df_data' in st.session_state:
        st.info("💡 اضغط على خلية REMARKS واختر الصنف الصحيح؛ سيتم تحديث السعر تلقائياً عند الاعتماد.")
        
        # استخدام st.data_editor لتمكين خاصية الـ EDIT
        edited_df = st.data_editor(
            st.session_state['df_data'],
            column_config={
                "REMARKS": st.column_config.SelectboxColumn(
                    "الصنف المختار (EDIT)",
                    options=st.session_state['m_options'],
                    width="large",
                    required=True
                )
            },
            disabled=[c_item, c_qty], # حماية البيانات الأصلية من التعديل
            use_container_width=True,
            key="matching_editor"
        )

        if st.button("🚀 اعتماد الاختيارات وحساب الأسعار"):
            price_map = st.session_state['price_dict']
            
            # تحديث السعر بناءً على القيمة المختارة في خانة REMARKS
            edited_df['Unit_Price'] = edited_df['REMARKS'].map(price_map).fillna(0)
            
            # إجراء العمليات الحسابية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            
            st.success("✅ تمت المطابقة وحساب الإجماليات!")
            st.dataframe(edited_df, use_container_width=True)
            
            st.metric("الإجمالي الكلي", f"{edited_df['Total'].sum():,.2f} EGP")
            
            # زر التحميل
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل عرض السعر النهائي", csv, "Quotation.csv", "text/csv")
