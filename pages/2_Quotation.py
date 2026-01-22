import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الاحترافي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر ليست لضمان تحديث الخيارات دائماً
def load_master_data():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master_data()

st.title("🛡️ نظام التسعير (قائمة منسدلة + إضافة يدوي)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col_a, col_b = st.columns(2)
    with col_a:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col_b:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns)

    if st.button("🔍 تحليل ومطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0)
        st.session_state['current_df'] = df_client

    if 'current_df' in st.session_state:
        st.success("💡 ملاحظة: عمود REMARKS يحتوي على خيارات الماستر، ويمكنك أيضاً مسحه وكتابة اسم جديد.")
        
        # إعداد محرر البيانات: REMARKS كقائمة منسدلة و Unit_Price قابل للتعديل
        edited_df = st.data_editor(
            st.session_state['current_df'],
            column_config={
                "REMARKS": st.column_config.SelectboxColumn(
                    "الصنف (EDIT)",
                    options=master_names, # ربط القائمة بالماستر ليست
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر (تعديل وحفظ)", 
                    format="%.2f",
                    min_value=0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="final_pricing_editor"
        )

        if st.button("🚀 اعتماد التسعير وحفظ البيانات الجديدة في الماستر"):
            new_items_to_add = []
            fresh_master, fresh_names = load_master_data()
            
            for index, row in edited_df.iterrows():
                final_name = str(row['REMARKS']).strip()
                final_price = float(row['Unit_Price'])
                
                # حفظ الصنف إذا كان اسماً جديداً تماماً كتبه المستخدم يدوياً
                if final_name not in fresh_names and final_name != "":
                    new_items_to_add.append({m_item: final_name, m_price: final_price})
                    fresh_names.append(final_name) # منع التكرار في نفس الجلسة
