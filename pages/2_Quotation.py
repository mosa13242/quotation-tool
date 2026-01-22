import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="تسعير طلبات العملاء", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر بأمان وتحديث قائمة الأسماء للبحث
def get_master_info():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).unique().tolist()
    return df, names

master_df, master_names = get_master_info()

st.title("💰 تسعير الطلبات (إكسيل + يدوي)")

# رفع الملف (يمكنك رفع أكثر من ملف أو ملف واحد)
uploaded_file = st.file_uploader("ارفع ملف الإكسيل للتسعير", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف في ملفك:", df_client.columns)
        c_qty = st.selectbox("عمود الكمية في ملفك:", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف في الماستر:", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر في الماستر:", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ المطابقة الذكية"):
        def match_logic(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        # الصنف الأصلي يظهر في خانة Item والمطابقة تظهر في REMARKS
        df_client['Item'] = df_client[c_item]
        df_client['REMARKS'] = df_client[c_item].apply(match_logic)
        
        # ربط الأسعار بناءً على عمود الملاحظات (REMARKS)
        p_lookup = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(p_lookup).fillna(0.0)
        
        # إعادة ترتيب الأعمدة كما طلبت
        st.session_state['priced_df'] = df_client[['Item', 'REMARKS', c_qty, 'Unit_Price']]

    if 'priced_df' in st.session_state:
        st.warning("💡 نظام البحث: امسح النص في REMARKS واكتب صنفاً جديداً ليتم حفظه تلقائياً في الماستر.")
        
        # جدول التسعير مع ميزة البحث والمسح
        final_edited = st.data_editor(
            st.session_state['priced_df'],
            column_config={
                "Item": st.column_config.TextColumn("الصنف المطلوب", disabled=True),
                "REMARKS": st.column_config.TextColumn(
                    "ملاحظات (البحث في الماستر)", 
                    suggestions=master_names, 
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f", min_value=0.0)
            },
            use_container_width=True,
            key="v_final_pricing"
        )

        if st.button("🚀 اعتماد الفاتورة وحفظ الأصناف الجديدة"):
            # إعادة تحميل الماستر لضمان عدم التكرار
            m_df, m_names = get_master_info()
            new_additions = []
            
            for idx, row in final_edited.iterrows():
                name_in_remarks = str(row['REMARKS']).strip()
                price_val = float(row['Unit_Price'])
                
                # إذا كتب صنفاً جديداً غير موجود في الماستر، أضفه
                if name_in_remarks != "" and name_in_remarks not in m_names:
                    new_additions.append({m_item: name_in_remarks, m_price: price_val})
                    m_names.append(name_in_remarks)

            if new_additions:
                new_df = pd.DataFrame(new_additions)
                updated_master = pd.concat([m_df, new_df], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_additions)} صنف جديد لملف الماستر!")

            # الحسابات النهائية للفاتورة
            final_edited[c_qty] = pd.to_numeric(final_edited[c_qty], errors='coerce').fillna(0)
            final_edited['Total'] = final_edited[c_qty] * final_edited['Unit_Price']
            st.write("### الفاتورة النهائية")
            st.dataframe(final_edited, use_container_width=True)
            st.metric("الإجمالي الكلي", f"{final_edited['Total'].sum():,.2f} EGP")


