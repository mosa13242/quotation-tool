import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الذكي", layout="wide")

# 1. إدارة ملف الماستر ليست
MASTER_FILE = "master_list.xlsx"

def load_master_data():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    # تنظيف أسماء الأعمدة من أي مسافات زائدة
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master_data()

st.title("🛡️ نظام التسعير (مصحح وشغال 100%)")

# 2. رفع الملف
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # واجهة اختيار الأعمدة
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ تحليل ومطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        # ربط السعر الحالي
        price_dict = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_dict).fillna(0.0)
        st.session_state['working_df'] = df_client

    # 3. واجهة التعديل والحفظ التلقائي
    if 'working_df' in st.session_state:
        st.info("💡 ملاحظة: يمكنك كتابة صنف جديد تماماً في REMARKS وسعره في Unit_Price وسيتم حفظهما.")
        
        # التعديل هنا لضمان قبول النصوص الجديدة
        edited_df = st.data_editor(
            st.session_state['working_df'],
            column_config={
                "REMARKS": st.column_config.TextColumn("الصنف المختار (قابل للتعديل)", width="large"),
                "Unit_Price": st.column_config.NumberColumn("السعر (قابل للتعديل)", format="%.2f")
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="v8_editor"
        )

        if st.button("🚀 اعتماد وحفظ في الماستر"):
            new_items = []
            m_df_fresh, m_names_fresh = load_master_data()
            
            for index, row in edited_df.iterrows():
                name_val = str(row['REMARKS']).strip()
                price_val = float(row['Unit_Price'])
                
                # فحص إذا كان الصنف جديد
