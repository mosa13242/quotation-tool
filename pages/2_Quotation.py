import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير الاحترافي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر لضمان تحديث قائمة البحث دائماً
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
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns)

    if st.button("🔍 تنفيذ المطابقة"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0.0)
        st.session_state['pricing_df'] = df_client

    if 'pricing_df' in st.session_state:
        st.success("💡 ميزة البحث: ابدأ الكتابة في REMARKS وستظهر لك اقتراحات الماستر.")
        
        # هنا دمجنا البحث (suggestions) مع الكتابة الحرة (TextColumn)
        edited_df = st.data_editor(
            st.session_state['pricing_df'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو كتابة جديد)",
                    suggestions=master_names,  # هذا هو عمود البحث
                    width="large",
                    required=True
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر (تعديل)", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="final_stable_editor"
        )

        if st.button("🚀 اعتماد وحفظ البيانات في الماستر"):
            new_items_found = []
            fresh_master, fresh_names = load_master_data()
            
            for index, row in edited_df.iterrows():
                name_val = str(row['REMARKS']).strip()
                price_val = float(row['Unit_Price'])
                
                # إذا كتبت صنفاً جديداً غير موجود في الماستر
                if name_val not in fresh_names and name_val != "":
                    new_items_found.append({m_item: name_val, m_price: price_val})
                    fresh_names.append(name_val)

            if new_items_found:
                new_data = pd.DataFrame(new_items_found)
                updated_master = pd.concat([fresh_master, new_data], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_items_found)} صنف جديد بأسعارهم!")

            # تحديث الحسابات النهائية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("إجمالي الفاتورة", f"{edited_df['Total'].sum():,.2f} EGP")
