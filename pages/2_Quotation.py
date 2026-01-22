import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير المستقر", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر - تضمن تحديث قائمة البحث دايماً
def load_master_data():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master_data()

st.title("🛡️ نظام التسعير (بحث ذكي + حفظ تلقائي)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (طلبك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلبك):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ المطابقة والبحث"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_lookup = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_lookup).fillna(0.0)
        st.session_state['df_working'] = df_client

    if 'df_working' in st.session_state:
        st.info("💡 اكتب في REMARKS للبحث، أو اكتب اسم جديد وسعر جديد للحفظ.")
        
        # التعديل اللي هيخلي البحث يظهر ويقبل الجديد
        edited_df = st.data_editor(
            st.session_state['df_working'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو جديد)",
                    suggestions=master_names,  # تفعيل قائمة البحث
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر (تعديل)", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="final_v20_stable"
        )

        if st.button("🚀 اعتماد وحفظ البيانات في الماستر"):
            new_entries = []
            f_master, f_names = load_master_data()
            
            for index, row in edited_df.iterrows():
                final_name = str(row['REMARKS']).strip()
                final_price = float(row['Unit_Price'])
                
                # إضافة الصنف الجديد للماستر فوراً
                if final_name not in f_names and final_name != "":
                    new_entries.append({m_item: final_name, m_price: final_price})
                    f_names.append(final_name)

            if new_entries:
                updated_master = pd.concat([f_master, pd.DataFrame(new_entries)], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_entries)} صنف جديد وسعرهم!")

            # تحديث الحسابات النهائية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي الكلي", f"{edited_df['Total'].sum():,.2f} EGP")
