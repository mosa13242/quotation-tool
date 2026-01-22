import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير المطور", layout="wide")

MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (تعديل وحفظ تلقائي)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns)

    if st.button("🔍 تحليل ومطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 65 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        # جلب السعر الحالي من الماستر
        price_dict = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_dict).fillna(0)
        st.session_state['df_edit'] = df_client

    if 'df_edit' in st.session_state:
        st.warning("✍️ عدل الاسم في REMARKS والسعر في Unit_Price ثم اضغط الزر بالأسفل للحفظ.")
        
        # تفعيل التعديل على REMARKS و Unit_Price
        edited_df = st.data_editor(
            st.session_state['df_edit'],
            column_config={
                "REMARKS": st.column_config.TextColumn("الصنف (قابل للتعديل)", width="large"),
                "Unit_Price": st.column_config.NumberColumn("السعر (قابل للتعديل)", format="%.2f")
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="editor_v4"
        )

        if st.button("🚀 اعتماد التسعير وحفظ التعديلات في الماستر"):
            new_items_to_save = []
            # استخراج قائمة الأصناف الحالية لتجنب التكرار
            current_master_items = master_df[m_item].astype(str).tolist()

            for index, row in edited_df.iterrows():
                name = str(row['REMARKS']).strip()
                price = float(row['Unit_Price'])
                
                # إذا كان الاسم جديداً أو السعر كان 0 وتم تعديله
                if name not in current_master_items and name != "":
                    new_items_to_save.append({m_item: name, m_price: price})
                    current_master_items.append(name) # منع التكرار في نفس العملية

            if new_items_to_save:
                new_df = pd.DataFrame(new_items_to_save)
                final_master = pd.concat([master_df, new_df], ignore_index=True)
                final_master.to_excel(MASTER_FILE, index=False)
