import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الذكي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل البيانات لضمان تحديث البحث دائماً
def load_master_list():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master_list()

st.title("🛡️ نظام التسعير (البحث والحفظ التلقائي)")

uploaded_file = st.file_uploader("ارفع ملف العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col_x, col_y = st.columns(2)
    with col_x:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col_y:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ مطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_lookup = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_lookup).fillna(0.0)
        st.session_state['working_df'] = df_client

    if 'working_df' in st.session_state:
        st.info("💡 اكتب في REMARKS للبحث، أو اكتب اسم جديد وسعر جديد للحفظ.")
        
        # هنا دمجنا البحث (suggestions) مع الكتابة الحرة (TextColumn)
        edited_df = st.data_editor(
            st.session_state['working_df'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو إضافة جديد)",
                    suggestions=master_names, # ميزة البحث والاقتراحات
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر (تعديل وحفظ)", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="final_v10_editor"
        )

        if st.button("🚀 اعتماد وحفظ البيانات في الماستر"):
            new_entries = []
            fresh_master, fresh_names = load_master_list()
            
            for index, row in edited_df.iterrows():
                item_name = str(row['REMARKS']).strip()
                item_price = float(row['Unit_Price'])
                
                # إذا كتبت اسم مش موجود في الماستر، هيحفظه هو وسعره الجديد
                if item_name not in fresh_names and item_name != "":
                    new_entries.append({m_item: item_name, m_price: item_price})
                    fresh_names.append(item_name)

            if new_entries:
                new_df = pd.DataFrame(new_entries)
                updated_master = pd.concat([fresh_master, new_df], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_entries)} صنف جديد وسعرهم للماستر!")

            # حساب الإجمالي النهائي
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي الكلي", f"{edited_df['Total'].sum():,.2f} EGP")
