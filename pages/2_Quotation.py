import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(layout="wide")
st.title("💰 نظام تسعير الطلبات")

# 1. إظهار زر الرفع أولاً لضمان عدم اختفائه
uploaded_file = st.file_uploader("📥 ارفع ملف العميل هنا (Excel)", type=["xlsx"])

MASTER_FILE = "master_list.xlsx"

def get_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).unique().tolist()

master_df, master_names = get_master()

if uploaded_file:
    try:
        df_client = pd.read_excel(uploaded_file)
        df_client.columns = [str(c).strip() for c in df_client.columns]
        
        # اختيار الأعمدة
        col1, col2 = st.columns(2)
        with col1:
            c_item = st.selectbox("عمود الصنف (طلب العميل):", df_client.columns)
            c_qty = st.selectbox("عمود الكمية (طلب العميل):", df_client.columns)
        with col2:
            m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns if not master_df.empty else ["Item"])
            m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns if not master_df.empty else ["Price"])

        if st.button("🔍 تنفيذ المطابقة والبحث"):
            def match_it(text):
                if not master_names: return str(text)
                match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
                return match if score > 70 else str(text)

            # توزيع البيانات: الأصلي في Item والمطابقة في REMARKS
            df_client['Item'] = df_client[c_item]
            df_client['REMARKS'] = df_client[c_item].apply(match_it)
            
            p_map = dict(zip(master_df[m_item], master_df[m_price]))
            df_client['Unit_Price'] = df_client['REMARKS'].map(p_map).fillna(0.0)
            st.session_state['v_data'] = df_client[['Item', 'REMARKS', c_qty, 'Unit_Price']]

        if 'v_data' in st.session_state:
            # محرر بيانات بسيط لتجنب TypeError
            final_df = st.data_editor(
                st.session_state['v_data'],
                column_config={
                    "Item": st.column_config.TextColumn("الصنف المطلوب", disabled=True),
                    "REMARKS": st.column_config.TextColumn("ملاحظات (بحث الماستر)", width="large"),
                    "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f")
                },
                use_container_width=True
            )

            if st.button("🚀 اعتماد وحفظ الأصناف الجديدة"):
                m_curr, m_names_curr = get_master()
                new_data = []
                for _, row in final_df.iterrows():
                    name = str(row['REMARKS']).strip()
                    price = float(row['Unit_Price'])
                    # إضافة الصنف للماستر إذا لم يكن موجوداً
                    if name != "" and name not in m_names_curr:
                        new_data.append({m_item: name, m_price: price})
                        m_names_curr.append(name)
                
                if new_data:
                    pd.concat([m_curr, pd.DataFrame(new_data)], ignore_index=True).to_excel(MASTER_FILE, index=False)
                    st.success("✅ تم تحديث الماستر لست بالأصناف والأسعار الجديدة!")

                # الحساب النهائي
                final_df[c_qty] = pd.to_numeric(final_df[c_qty], errors='coerce').fillna(0)
                final_df['Total'] = final_df[c_qty] * final_df['Unit_Price']
                st.dataframe(final_df, use_container_width=True)
                st.metric("الإجمالي", f"{final_df['Total'].sum():,.2f} EGP")

    except Exception as e:
        st.error(f"خطأ: {e}")
else:
    st.info("💡 خانة الرفع موجودة في الأعلى. ارفع ملف إكسيل للبدء.")

