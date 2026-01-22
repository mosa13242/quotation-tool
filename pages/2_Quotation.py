import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير والبحث", layout="wide")

MASTER_FILE = "master_list.xlsx"

# وظيفة تحميل الماستر بأمان وتحديث قائمة الأسماء للبحث
def load_master_data():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    # استخراج قائمة الأصناف لاستخدامها في ميزة البحث (Suggestions)
    names_list = df[df.columns[0]].astype(str).unique().tolist()
    return df, names_list

master_df, master_names = load_master_data()

st.title("🛡️ نظام التسعير الذكي (بحث + إضافة)")

# 1. واجهة رفع الملف
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # اختيار الأعمدة للمطابقة
    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with col2:
        m_item = st.selectbox("عمود الصنف (الماستر):", master_df.columns if not master_df.empty else ["Item"])
        m_price = st.selectbox("عمود السعر (الماستر):", master_df.columns if not master_df.empty else ["Price"])

    # 2. تفعيل المطابقة الذكية
    if st.button("🔍 تنفيذ المطابقة والبحث الذكي"):
        def match_logic(text):
            if not master_names: return str(text)
            # البحث عن أقرب تطابق في الماستر بنسبة دقة أعلى من 70%
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 70 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(match_logic)
        price_lookup = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_lookup).fillna(0.0)
        st.session_state['current_quote'] = df_client

    # 3. جدول التعديل وتفعيل نظام البحث (Suggestions)
    if 'current_quote' in st.session_state:
        st.info("💡 نظام البحث: ابدأ الكتابة في خانة REMARKS لتظهر لك الأصناف المسجلة، أو اكتب صنفاً جديداً.")
        
        # استخدام TextColumn مع Suggestions لتوفير تجربة بحث وسلسة
        edited_df = st.data_editor(
            st.session_state['current_quote'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو جديد)",
                    help="يمكنك الاختيار من القائمة أو كتابة اسم جديد تماماً",
                    suggestions=master_names, # تفعيل قائمة البحث المنسدلة
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر الجديد", 
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty], # منع تعديل بيانات العميل الأصلية
            use_container_width=True,
            key="pricing_editor_v3"
        )

        # 4. حفظ الأصناف الجديدة والأسعار في الماستر
        if st.button("🚀 اعتماد الفاتورة وحفظ الأصناف الجديدة"):
            latest_master, latest_names = load_master_data()
            new_entries = []
            
            for _, row in edited_df.iterrows():
                final_name = str(row['REMARKS']).strip()
                final_price = float(row['Unit_Price'])
                
                # إذا كان الاسم جديداً وغير موجود في قائمة الماستر، يتم حفظه
                if final_name != "" and final_name not in latest_names:
                    new_entries.append({m_item: final_name, m_price: final_price})
                    latest_names.append(final_name) # منع التكرار في نفس العملية

            if new_entries:
                updated_df = pd.concat([latest_master, pd.DataFrame(new_entries)], ignore_index=True)
                updated_df.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_entries)} صنف جديد لملف الماستر بنجاح!")

            # عرض النتائج النهائية والحسابات
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            st.write("### مراجعة الفاتورة النهائية:")
            st.dataframe(edited_df, use_container_width=True)
            st.metric("إجمالي القيمة", f"{edited_df['Total'].sum():,.2f} EGP")

