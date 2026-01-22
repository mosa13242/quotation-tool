import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير المستقر", layout="wide")

MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).unique().tolist()
    return df, names

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (النسخة المستقرة)")

uploaded_file = st.file_uploader("ارفع ملف الإكسيل", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (طلبك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلبك):", df_client.columns)
    with col2:
        m_item = st.selectbox("صنف الماستر:", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("سعر الماستر:", master_df.columns if not master_df.empty else ["Price"])

    # تنفيذ المطابقة الأولية
    if st.button("🔍 تنفيذ المطابقة الذكية"):
        def quick_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['Item'] = df_client[c_item]
        df_client['REMARKS'] = df_client[c_item].apply(quick_match)
        price_dict = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_dict).fillna(0.0)
        st.session_state['v_data'] = df_client[['Item', 'REMARKS', c_qty, 'Unit_Price']]

    if 'v_data' in st.session_state:
        # حل مشكلة البحث: شريط بحث خارجي لتجنب أخطاء الجدول
        st.markdown("---")
        st.subheader("🔎 مساعد البحث السريع")
        search_query = st.text_input("ابحث عن صنف في الماستر لنسخ اسمه:")
        if search_query:
            results = process.extract(search_query, master_names, limit=5)
            st.write("أصناف مقترحة (انسخ الاسم وضعه في الجدول):")
            for r in results:
                st.code(r[0]) # يظهر الاسم في صندوق كود ليسهل نسخه بضغطة واحدة

        # الجدول التفاعلي (تم حذف suggestions لتجنب TypeError)
        edited_df = st.data_editor(
            st.session_state['v_data'],
            column_config={
                "Item": st.column_config.TextColumn("الصنف المطلوب", disabled=True),
                "REMARKS": st.column_config.TextColumn("ملاحظات (اكتب أو الصق الاسم هنا)", width="large"),
                "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f")
            },
            use_container_width=True,
            key="stable_editor_v4"
        )

        if st.button("🚀 اعتماد وحفظ"):
            m_df, m_names = load_master()
            new_additions = []
            for _, row in edited_df.iterrows():
                name = str(row['REMARKS']).strip()
                price = float(row['Unit_Price'])
                if name != "" and name not in m_names:
                    new_additions.append({m_item: name, m_price: price})
                    m_names.append(name)
            
            if new_additions:
                pd.concat([m_df, pd.DataFrame(new_additions)], ignore_index=True).to_excel(MASTER_FILE, index=False)
                st.success("✅ تم تحديث الماستر بالبيانات الجديدة!")

            # الحسابات النهائية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")

