import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير والبحث الذكي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر وتحديث القائمة بأمان
def get_master_data():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    # قائمة الأسماء لتغذية نظام البحث (Suggestions)
    names = df[df.columns[0]].astype(str).unique().tolist()
    return df, names

master_df, master_names = get_master_data()

st.title("🛡️ نظام التسعير (بحث + إضافة + حفظ)")

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

    # زر تنفيذ البحث الذكي والمطابقة
    if st.button("🔍 تنفيذ المطابقة الذكية"):
        def find_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(find_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0.0)
        st.session_state['df_working'] = df_client

    if 'df_working' in st.session_state:
        st.info("💡 نظام البحث فعال: ابدأ الكتابة في خانة REMARKS لتظهر الاقتراحات؛ الأسماء والأسعار الجديدة ستحفظ تلقائياً.")
        
        # استخدام TextColumn بشكل صحيح لتفعيل البحث والمسح
        edited_df = st.data_editor(
            st.session_state['df_working'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو إضافة)",
                    suggestions=master_names,
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر الجديد", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="v_final_stable_editor"
        )

        if st.button("🚀 اعتماد وحفظ الأصناف الجديدة"):
            # إعادة تحميل البيانات لضمان عدم التكرار
            f_master, f_names = get_master_data()
            new_rows = []
            
            for idx, row in edited_df.iterrows():
                row_name = str(row['REMARKS']).strip()
                row_price = float(row['Unit_Price'])
                
                # تخزين الصنف الجديد مع سعره اليدوي في الماستر
                if row_name not in f_names and row_name != "":
                    new_rows.append({m_item: row_name, m_price: row_price})
                    f_names.append(row_name)

            if new_rows:
                updated_master = pd.concat([f_master, pd.DataFrame(new_rows)], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_rows)} صنف جديد لملف الماستر!")

            # عرض الحسابات الختامية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي الكلي", f"{edited_df['Total'].sum():,.2f} EGP")

