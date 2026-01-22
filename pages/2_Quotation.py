import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="تسعير طلبات العملاء", layout="wide")
MASTER_FILE = "master_list.xlsx"

def load_master_safe():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).unique().tolist()
    return df, names

master_df, master_names = load_master_safe()

st.title("💰 تسعير الطلبات (إكسيل + يدوي)")

# دعم رفع عدة ملفات أو ملف واحد كما طلبت
uploaded_files = st.file_uploader("ارفع ملفات الإكسيل للتسعير", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    # دمج كافة الملفات المرفوعة في جدول واحد
    all_data = [pd.read_excel(f) for f in uploaded_files]
    df_client = pd.concat(all_data, ignore_index=True)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (طلب العميل):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلب العميل):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ المطابقة الذكية"):
        def match_func(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        # الصنف المطلوب تحت Item والمطابقة تحت REMARKS
        df_client['Item'] = df_client[c_item]
        df_client['REMARKS'] = df_client[c_item].apply(match_func)
        
        # جلب السعر بناءً على REMARKS
        price_lookup = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_lookup).fillna(0.0)
        
        st.session_state['priced_data'] = df_client[['Item', 'REMARKS', c_qty, 'Unit_Price']]

    if 'priced_data' in st.session_state:
        st.info("💡 نظام البحث: ابدأ الكتابة في REMARKS لتظهر الأصناف؛ والأسماء الجديدة ستحفظ تلقائياً.")
        
        # الجدول التفاعلي الخالي من أخطاء الـ Syntax
        final_df = st.data_editor(
            st.session_state['priced_data'],
            column_config={
                "Item": st.column_config.TextColumn("الصنف المطلوب", disabled=True),
                "REMARKS": st.column_config.TextColumn("ملاحظات (البحث في الماستر)", suggestions=master_names, width="large"),
                "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f", min_value=0.0)
            },
            use_container_width=True,
            key="v_final_pricing_stable"
        )

        if st.button("🚀 اعتماد وحفظ الأصناف الجديدة في الماستر"):
            current_m, current_names = load_master_safe()
            new_rows = []
            
            for _, row in final_df.iterrows():
                remark_name = str(row['REMARKS']).strip()
                price_val = float(row['Unit_Price'])
                
                # إضافة الصنف الجديد للماستر فوراً
                if remark_name != "" and remark_name not in current_names:
                    new_rows.append({m_item: remark_name, m_price: price_val})
                    current_names.append(remark_name)

            if new_rows:
                updated_master = pd.concat([current_m, pd.DataFrame(new_rows)], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_additions)} صنف جديد للماستر!")

            # الحسابات النهائية
            final_df[c_qty] = pd.to_numeric(final_df[c_qty], errors='coerce').fillna(0)
            final_df['Total'] = final_df[c_qty] * final_df['Unit_Price']
            st.dataframe(final_df, use_container_width=True)
            st.metric("الإجمالي النهائي", f"{final_df['Total'].sum():,.2f} EGP")

