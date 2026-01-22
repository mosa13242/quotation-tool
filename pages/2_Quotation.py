import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير والتعلم الذكي", layout="wide")

# 1. وظيفة تحميل وتحديث الماستر ليست
MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        # إنشاء ملف جديد إذا لم يكن موجوداً
        df_new = pd.DataFrame(columns=["Item", "Price"])
        df_new.to_excel(MASTER_FILE, index=False)
        return df_new, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (تسجيل وحفظ الأصناف الجديدة)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    # إعدادات الربط
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    if st.button("🔍 تنفيذ مطابقة وتحليل"):
        def smart_match(text):
            if not master_names: return str(text)
            # البحث عن كلمات مشتركة مثل CANNULA
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 60 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        st.session_state['df_working'] = df_client

    # --- واجهة الـ EDIT المفتوحة (تسمح بكتابة أي شيء) ---
    if 'df_working' in st.session_state:
        st.info("💡 يمكنك الآن مسح أي خلية في REMARKS وكتابة صنف جديد تماماً، وسيتم حفظه فوراً.")
        
        # تحويل REMARKS لعمود نصي عادي بدلاً من Selectbox لتجنب المسح التلقائي
        edited_df = st.data_editor(
            st.session_state['df_working'],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف المختار (اكتب الجديد هنا)",
                    help="اكتب اسم الصنف كما تريده أن يظهر في الماستر ليست",
                    width="large"
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="smart_editor_v2"
        )

        if st.button("🚀 اعتماد التسعير وحفظ في الماستر"):
            price_dict = dict(zip(master_df[m_item], master_df[m_price]))
            new_items_list = []

            # فحص المدخلات الجديدة
            for index, row in edited_df.iterrows():
                val = str(row['REMARKS']).strip()
                if val not in master_names and val != "":
                    new_items_list.append({m_item: val, m_price: 0})
                    master_names.append(val)

            # تحديث ملف الماستر فعلياً
            if new_items_list:
                new_entries_df = pd.DataFrame(new_items_list)
                updated_master = pd.concat([master_df, new_entries_df], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم تسجيل {len(new_items_list)} صنف جديد في الماستر ليست!")

            # حساب الأسعار النهائية
            edited_df['Unit_Price'] = edited_df['REMARKS'].map(price_dict).fillna(0)
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            
            st.success("✅ تم تحديث الأسعار بناءً على مدخلاتك.")
            st.dataframe(edited_df, use_container_width=True)
            
            st.metric("الإجمالي", f"{edited_df['Total'].sum():,.2f} EGP")
            
            # تصدير الملف
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الإكسيل المسعر", csv, "Quotation_Final.csv", "text/csv")
