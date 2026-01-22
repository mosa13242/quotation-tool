import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الذكي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# تحميل بيانات الماستر لضمان وجود قائمة البحث دايماً
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

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col_a, col_b = st.columns(2)
    with col_a:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col_b:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ مطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0.0)
        st.session_state['df_pricing'] = df_client

    if 'df_pricing' in st.session_state:
        st.info("💡 البحث شغال: اكتب في REMARKS وهتظهرلك الاقتراحات؛ أو اكتب اسم وسعر جديد وهيتحفظوا.")
        
        # هنا دمجنا البحث (suggestions) مع الكتابة الحرة (TextColumn)
        edited_df = st.data_editor(
            st.session_state['df_pricing'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو اكتب جديداً)",
                    suggestions=master_names, # ميزة البحث والاقتراحات
                    width="large",
                    required=True
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر (تعديل وحفظ)", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="v11_stable_editor"
        )

        if st.button("🚀 اعتماد وحفظ الأصناف والأسعار"):
            new_records = []
            m_df_fresh, m_names_fresh = load_master_list()
            
            for index, row in edited_df.iterrows():
                r_name = str(row['REMARKS']).strip()
                r_price = float(row['Unit_Price'])
                
                # لو كتبت اسم جديد مش موجود في الماستر، هيضيفه هو وسعره
                if r_name not in m_names_fresh and r_name != "":
                    new_records.append({m_item: r_name, m_price: r_price})
                    m_names_fresh.append(r_name)

            if new_records:
                new_data = pd.DataFrame(new_records)
                updated_master = pd.concat([m_df_fresh, new_data], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم تسجيل {len(new_records)} صنف جديد بأسعارهم في الماستر!")

            # تحديث الحسابات النهائية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")
