import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير المستقر", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر - تضمن تحديث قائمة البحث دايماً
def load_master_safe():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master_safe()

st.title("🛡️ نظام التسعير (بحث + إضافة + حفظ)")

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

    if st.button("🔍 تنفيذ المطابقة والبحث"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0.0)
        st.session_state['df_working'] = df_client

    if 'df_working' in st.session_state:
        st.success("💡 ميزة البحث: ابدأ الكتابة في REMARKS للاختيار، أو اكتب اسماً جديداً وسعراً لحفظهما.")
        
        # دمج البحث مع الكتابة الحرة باستخدام TextColumn
        edited_df = st.data_editor(
            st.session_state['df_working'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو جديد)",
                    suggestions=master_names,  # تفعيل البحث والاقتراحات
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
            key="final_stable_editor_v15"
        )

        if st.button("🚀 اعتماد وحفظ التعديلات في الماستر"):
            new_rows = []
            m_df_fresh, m_names_fresh = load_master_safe()
            
            for index, row in edited_df.iterrows():
                name_val = str(row['REMARKS']).strip()
                price_val = float(row['Unit_Price'])
                
                # حفظ الصنف الجديد مع سعره المكتوب يدوياً
                if name_val not in m_names_fresh and name_val != "":
                    new_rows.append({m_item: name_val, m_price: price_val})
                    m_names_fresh.append(name_val)

            if new_rows:
                new_data = pd.DataFrame(new_rows)
                updated_master = pd.concat([m_df_fresh, new_data], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_rows)} صنف جديد بأسعارهم في الماستر!")

            # تحديث العرض النهائي والحسابات
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي النهائي", f"{edited_df['Total'].sum():,.2f} EGP")
