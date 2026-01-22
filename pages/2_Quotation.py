import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام تسعير الأصناف الجديدة", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة لتحميل الماستر والحصول على قائمة الأسماء المحدثة
def get_updated_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names_list = df[df.columns[0]].astype(str).tolist()
    return df, names_list

master_df, master_names = get_updated_master()

st.title("🛠️ نظام التسعير (مسح، كتابة، وحفظ تلقائي)")

uploaded_file = st.file_uploader("ارفع ملف طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (طلب العميل):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلب العميل):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns if not master_df.empty else ["Price"])

    if st.button("🔍 تنفيذ البحث والمطابقة الأولية"):
        def initial_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(initial_match)
        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_map).fillna(0.0)
        st.session_state['df_quotation'] = df_client

    if 'df_quotation' in st.session_state:
        st.warning("⚠️ يمكنك الآن مسح أي كلمة في REMARKS وكتابة صنف جديد، ثم وضع سعره يدوياً.")
        
        # تفعيل خاصية التعديل الحر والبحث (Suggestions)
        edited_df = st.data_editor(
            st.session_state['df_quotation'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (امسح واكتب الجديد هنا)",
                    help="يمكنك مسح المحتوى وكتابة اسم صنف جديد تماماً",
                    suggestions=master_names, # تظهر كخيارات لكنها لا تمنع الكتابة الجديدة
                    required=True
                ),
                "Unit_Price": st.column_config.NumberColumn("السعر الجديد", format="%.2f")
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="v2_editor"
        )

        if st.button("🚀 اعتماد الأسعار وحفظ الأصناف الجديدة في الماستر"):
            # إعادة تحميل الماستر لضمان عدم التكرار
            current_master, current_names = get_updated_master()
            new_records = []
            
            for index, row in edited_df.iterrows():
                final_name = str(row['REMARKS']).strip()
                final_price = float(row['Unit_Price'])
                
                # التحقق: إذا كان الصنف غير موجود في الماستر، يتم إضافته تلقائياً
                if final_name != "" and final_name not in current_names:
                    new_records.append({m_item: final_name, m_price: final_price})
                    current_names.append(final_name) # لمنع تكرار نفس الصنف في نفس الجلسة
            
            if new_records:
                new_df = pd.DataFrame(new_records)
                updated_master = pd.concat([current_master, new_df], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_records)} أصناف جديدة بأسعارها في ملف الماستر!")
            else:
                st.info("ℹ️ لم يتم العثور على أصناف جديدة لإضافتها.")

            # عرض النتيجة النهائية مع الحسابات
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.write("### الفاتورة النهائية:")
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي الكلي", f"{edited_df['Total'].sum():,.2f} EGP")


