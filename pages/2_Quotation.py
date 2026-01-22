import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير والتعلم الذكي", layout="wide")

# 1. تحميل وتحديث الماستر ليست
MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        st.error("❌ ملف الماستر غير موجود.")
        return pd.DataFrame(), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (إضافة تلقائية للماستر)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تحليل ومطابقة"):
        def smart_match(text):
            if not master_names: return "⚠️ صنف جديد"
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 60 else "⚠️ صنف جديد"

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        st.session_state['df'] = df_client

    if 'df' in st.session_state:
        st.info("💡 يمكنك كتابة اسم صنف جديد تماماً في REMARKS وسيحفظ في الماستر تلقائياً.")
        
        # تفعيل خاصية الكتابة الحرة في عمود الاختيارات
        edited_df = st.data_editor(
            st.session_state['df'],
            column_config={
                "REMARKS": st.column_config.SelectboxColumn(
                    "الصنف (EDIT)",
                    options=master_names,
                    required=True,
                )
            },
            use_container_width=True,
            key="master_editor"
        )

        if st.button("🚀 اعتماد وحفظ الأصناف الجديدة"):
            price_dict = dict(zip(master_df[m_item], master_df[m_price])) if not master_df.empty else {}
            new_rows_to_add = []

            # معالجة كل سطر
            for index, row in edited_df.iterrows():
                chosen_name = row['REMARKS']
                # إذا كان الاسم جديداً وغير موجود في الماستر
                if chosen_name not in master_names and chosen_name != "⚠️ صنف جديد":
                    new_rows_to_add.append({m_item: chosen_name, m_price: 0}) # يضاف بسعر 0 ليعدل لاحقاً
                    master_names.append(chosen_name) # إضافة مؤقتة للقائمة

            # تحديث ملف الإكسيل الفعلي (الماستر ليست)
            if new_rows_to_add:
                new_items_df = pd.DataFrame(new_rows_to
