import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="تسعير الطلبات", layout="wide")

MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ تسعير الطلبات (بحث + إضافة + حفظ)")

# رفع الملف
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (طلبك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلبك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ المطابقة الذكية"):
        def find_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(find_search_match if 'find_search_match' in locals() else find_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0.0)
        st.session_state['working_df'] = df_client

    if 'working_df' in st.session_state:
        st.info("💡 امسح النص في REMARKS واكتب صنفاً جديداً خالصاً وسعره لحفظهما.")
        
        # الجدول التفاعلي
        edited_df = st.data_editor(
            st.session_state['working_df'],
            column_config={
                "REMARKS": st.column_config.TextColumn("الصنف (بحث أو جديد)", suggestions=master_names, width="large"),
                "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f")
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="final_editor_stable"
        )

        if st.button("🚀 حفظ الأسعار والأصناف الجديدة"):
            fresh_m, fresh_names = load_master()
            new_rows = []
            for _, row in edited_df.iterrows():
                name, price = str(row['REMARKS']).strip(), float(row['Unit_Price'])
                if name != "" and name not in fresh_names:
                    new_rows.append({m_item: name, m_price: price})
                    fresh_names.append(name)

            if new_rows:
                pd.concat([fresh_m, pd.DataFrame(new_rows)], ignore_index=True).to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_rows)} صنف جديد للماستر!")

            # الحسابات النهائية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي الكلي", f"{edited_df['Total'].sum():,.2f} EGP")
