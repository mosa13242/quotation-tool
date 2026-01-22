import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="إصدار كوتيشن", layout="wide")
MASTER_FILE = "master_list.xlsx"

# وظيفة لتحميل بيانات الماستر وتحديث قائمة الاقتراحات
def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    # قائمة الأسماء لاستخدامها في ميزة البحث (Suggestions)
    names_list = df[df.columns[0]].astype(str).tolist()
    return df, names_list

master_df, master_names = load_master()

st.title("🔍 نظام التسعير (بحث + إضافة + حفظ)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🚀 تنفيذ مطابقة وبدء البحث"):
        def match_logic(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(match_logic)
        p_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(p_map).fillna(0.0)
        st.session_state['active_df'] = df_client

    if 'active_df' in st.session_state:
        st.success("💡 ميزة البحث: ابدأ الكتابة في REMARKS لتظهر الاقتراحات؛ أو اكتب صنفاً وسعراً جديداً.")

        # التعديل الصحيح والمستقر لعمود البحث والكتابة
        edited_df = st.data_editor(
            st.session_state['active_df'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو إضافة)",
                    suggestions=master_names, # تفعيل الاقتراحات
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="v30_stable_editor"
        )

        if st.button("💾 حفظ الأصناف والأسعار الجديدة في الماستر"):
            new_data_list = []
            m_fresh, m_names_fresh = load_master()
            
            for i, row in edited_df.iterrows():
                row_name = str(row['REMARKS']).strip()
                row_price = float(row['Unit_Price'])
                
                # حفظ الصنف الجديد مع سعره اليدوي في الماستر
                if row_name not in m_names_fresh and row_name != "":
                    new_data_list.append({m_item: row_name, m_price: row_price})
                    m_names_fresh.append(row_name)

            if new_data_list:
                updated_master = pd.concat([m_fresh, pd.DataFrame(new_data_list)], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم تسجيل {len(new_data_list)} صنف جديد وسعره في الماستر!")

            # تحديث الحسابات النهائية
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")
