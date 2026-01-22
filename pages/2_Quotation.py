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

st.title("🛡️ نظام التسعير (بحث + إضافة صنف وسعر جديد)")

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

    if st.button("🔍 تنفيذ تحليل ومطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_dict = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_dict).fillna(0.0)
        st.session_state['df_final'] = df_client

    if 'df_final' in st.session_state:
        st.info("💡 ابحث في REMARKS أو اكتب صنفاً جديداً وسعره ثم اضغط 'اعتماد'.")
        
        # استخدام TextColumn مع خاصية الاقتراحات (Suggestions) لتوفير البحث
        edited_df = st.data_editor(
            st.session_state['df_final'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (ابحث أو اكتب جديداً)",
                    help="ابدأ الكتابة للبحث في الماستر، أو اكتب اسماً جديداً تماماً",
                    width="large",
                    required=True,
                    # هذه هي ميزة البحث والاقتراحات
                    suggestions=master_names 
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر (قابل للتعديل)",
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="v9_stable_editor"
        )

        if st.button("🚀 اعتماد وحفظ التعديلات"):
            new_rows = []
            fresh_master, fresh_names = load_master()
            
            for index, row in edited_df.iterrows():
                name = str(row['REMARKS']).strip()
                price = float(row['Unit_Price'])
                
                # إذا كان الصنف جديداً تماماً، نضيفه للماستر بالاسم والسعر المكتوبين
                if name not in fresh_names and name != "":
                    new_rows.append({m_item: name, m_price: price})
                    fresh_names.append(name)

            if new_rows:
                new_data = pd.DataFrame(new_rows)
                updated_master = pd.concat([fresh_master, new_data], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_rows)} صنف جديد بأسعارهم للماستر!")

            # تحديث الحسابات للعرض
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")
