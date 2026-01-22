import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

# إعداد الصفحة وتأمين ظهور زر الرفع
st.set_page_config(page_title="نظام التسعير المستقر", layout="wide")

MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).unique().tolist()
    return df, names

master_df, master_names = load_master()

st.title("💰 نظام تسعير الطلبات (بحث + مطابقة)")

# 1. زر رفع الملف (أول عنصر لضمان ظهوره)
uploaded_file = st.file_uploader("📥 ارفع ملف العميل (Excel)", type=["xlsx"])

if uploaded_file:
    try:
        df_client = pd.read_excel(uploaded_file)
        df_client.columns = [str(c).strip() for c in df_client.columns]
        
        # اختيار الأعمدة
        col1, col2 = st.columns(2)
        with col1:
            c_item = st.selectbox("عمود الصنف (طلبك):", df_client.columns)
            c_qty = st.selectbox("عمود الكمية (طلبك):", df_client.columns)
        with col2:
            m_item = st.selectbox("صنف الماستر:", master_df.columns if not master_df.empty else ["Item"])
            m_price = st.selectbox("سعر الماستر:", master_df.columns if not master_df.empty else ["Price"])

        # 2. تنفيذ المطابقة الذكية الأولية
        if st.button("🔍 تنفيذ المطابقة الذكية"):
            def quick_match(text):
                if not master_names: return str(text)
                match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
                return match if score > 70 else str(text)

            # توزيع البيانات كما طلبت
            df_client['Item'] = df_client[c_item] # الصنف المطلوب
            df_client['REMARKS'] = df_client[c_item].apply(quick_match) # المطابقة أو البحث
            
            p_dict = dict(zip(master_df[m_item], master_df[m_price]))
            df_client['Unit_Price'] = df_client['REMARKS'].map(p_dict).fillna(0.0)
            
            st.session_state['data_v5'] = df_client[['Item', 'REMARKS', c_qty, 'Unit_Price']]

        if 'data_v5' in st.session_state:
            # 3. نظام البحث المساعد (لتجنب TypeError داخل الجدول)
            st.markdown("---")
            st.subheader("🔎 مساعد البحث في الماستر")
            search_query = st.text_input("ابحث عن اسم صنف لنسخه وضعه في REMARKS:")
            if search_query:
                matches = process.extract(search_query, master_names, limit=3)
                for m in matches:
                    st.code(m[0]) # يظهر الاسم في صندوق كود لتسهيل النسخ

            # 4. جدول التعديل المستقر (تم إلغاء suggestions المسببة للخطأ)
            edited_df = st.data_editor(
                st.session_state['data_v5'],
                column_config={
                    "Item": st.column_config.TextColumn("الصنف المطلوب", disabled=True),
                    "REMARKS": st.column_config.TextColumn("ملاحظات (البحث والمطابقة)", width="large"),
                    "Unit_Price": st.column_config.NumberColumn("السعر", format="%.2f")
                },
                use_container_width=True,
                key="v5_stable_pricing"
            )

            # 5. الحفظ النهائي وتحديث الماستر
            if st.button("🚀 اعتماد الفاتورة وحفظ الأصناف الجديدة"):
                m_df, m_names = load_master()
                new_data = []
                for _, row in edited_df.iterrows():
                    r_name = str(row['REMARKS']).strip()
                    r_price = float(row['Unit_Price'])
                    if r_name != "" and r_name not in m_names:
                        new_data.append({m_item: r_name, m_price: r_price})
                        m_names.append(r_name)
                
                if new_data:
                    pd.concat([m_df, pd.DataFrame(new_data)], ignore_index=True).to_excel(MASTER_FILE, index=False)
                    st.success("✅ تم تحديث الماستر بالأصناف الجديدة!")

                # عرض الحسابات
                edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
                edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
                st.dataframe(edited_df, use_container_width=True)
                st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")

    except Exception as e:
        st.error(f"خطأ في معالجة البيانات: {e}")
else:
    st.info("يرجى رفع ملف إكسيل للبدء.")

