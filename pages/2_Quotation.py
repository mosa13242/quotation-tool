import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(layout="wide")
st.title("💰 نظام التسعير")

# 1. زر الرفع في المقدمة لضمان ظهوره
uploaded_file = st.file_uploader("📥 ارفع ملف طلب العميل (Excel)", type=["xlsx"])

MASTER_FILE = "master_list.xlsx"

def get_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    # التأكد من أن الأسعار أرقام وليست نصوصاً
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors='coerce').fillna(0.0)
    return df, df[df.columns[0]].astype(str).unique().tolist()

master_df, master_names = get_master()

if uploaded_file:
    try:
        df_client = pd.read_excel(uploaded_file)
        df_client.columns = [str(c).strip() for c in df_client.columns]
        
        col1, col2 = st.columns(2)
        with col1:
            c_item = st.selectbox("عمود الصنف (طلبك):", df_client.columns)
            c_qty = st.selectbox("عمود الكمية (طلبك):", df_client.columns)
        with col2:
            m_item = st.selectbox("الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
            m_price = st.selectbox("السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

        if st.button("🔍 تنفيذ المطابقة والبحث"):
            def match_it(text):
                if not master_names: return str(text)
                match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
                return match if score > 70 else str(text)

            # توزيع البيانات كما طلبت
            df_client['Item'] = df_client[c_item]
            df_client['REMARKS'] = df_client[c_item].apply(match_it)
            
            p_map = dict(zip(master_df[m_item], master_df[m_price]))
            # تحويل السعر لرقم عشري ومنع ظهور خطأ 'f'
            df_client['Unit_Price'] = df_client['REMARKS'].map(p_map).fillna(0.0)
            df_client['Unit_Price'] = pd.to_numeric(df_client['Unit_Price'], errors='coerce').fillna(0.0)
            
            st.session_state['priced_v14'] = df_client[['Item', 'REMARKS', c_qty, 'Unit_Price']]

        if 'priced_v14' in st.session_state:
            # التعديل النهائي بدون أخطاء تنسيق
            edited_df = st.data_editor(
                st.session_state['priced_v14'],
                column_config={
                    "Item": st.column_config.TextColumn("الصنف المطلوب", disabled=True),
                    "REMARKS": st.column_config.TextColumn("ملاحظات (البحث في الماستر)", width="large"),
                    "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f") # تم تأمينها لتكون أرقاماً فقط
                },
                use_container_width=True
            )

            if st.button("🚀 اعتماد وحفظ"):
                # حسابات الإجمالي النهائي
                edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
                edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
                st.dataframe(edited_df, use_container_width=True)
                st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")

