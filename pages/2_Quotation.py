import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير والتعلم الذكي", layout="wide")

# 1. وظيفة تحميل وتحديث الماستر ليست
MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "Price"]), ["Item"]
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (إضافة وحفظ الأصناف الجديدة)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # إعدادات الربط لتجنب KeyError
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    if st.button("🔍 تنفيذ مطابقة أولية"):
        def smart_match(text):
            # استخدام مطابقة الكلمات المفتاحية (مثل CANNULA)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 60 else "⚠️ صنف جديد (اكتبه يدوياً)"

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        st.session_state['df_working'] = df_client

    # --- واجهة الـ EDIT والتعلم التلقائي ---
    if 'df_working' in st.session_state:
        st.info("💡 يمكنك مسح المكتوب في REMARKS وكتابة اسم صنف جديد تماماً ليتم حفظه.")
        
        # استخدام st.data_editor للسماح بالكتابة الحرة
        edited_df = st.data_editor(
            st.session_state['df_working'],
            column_config={
                "REMARKS": st.column_config.SelectboxColumn(
                    "الصنف المختار (EDIT)",
                    options=master_names,
                    required=True,
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="smart_editor"
        )

        if st.button("🚀 اعتماد التسعير وحفظ الأصناف الجديدة"):
            # تجهيز قاموس الأسعار الحالي
            price_dict = dict(zip(master_df[m_item], master_df[m_price]))
            new_items_found = []

            # فحص كل سطر في الجدول المعدل
            for index, row in edited_df.iterrows():
                chosen_name = str(row['REMARKS']).strip()
                
                # إذا قام المستخدم بكتابة صنف غير موجود في الماستر
                if chosen_name not in master_names and chosen_name != "⚠️ صنف جديد (اكتبه يدوياً)":
                    new_items_found.append({m_item: chosen_name, m_price: 0})
                    master_names.append(chosen_name) # إضافة مؤقتة للقائمة المنسدلة

            # حفظ الأصناف الجديدة في ملف الماستر فعلياً
            if new_items_found:
                new_df = pd.DataFrame(new_items_found)
                updated_master = pd.concat([master_df, new_df], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_items_found)} صنف جديد في الماستر ليست!")

            # حساب التسعير النهائي بناءً على الاختيارات
            edited_df['Unit_Price'] = edited_df['REMARKS'].map(price_dict).fillna(0)
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            
            st.dataframe(edited_df, use_container_width=True)
            st.metric("إجمالي عرض السعر", f"{edited_df['Total'].sum():,.2f} EGP")
            
            # تصدير النتيجة
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الإكسيل المسعر", csv, "Quotation.csv", "text/csv")
