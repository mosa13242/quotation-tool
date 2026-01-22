import streamlit as st
import pandas as pd
import difflib

st.set_page_config(page_title="Quotation Tool 2.0", layout="wide")

st.title("Quotation Tool 2.0 (Auto-Pricing)")

# --- 1. معالجة ملف الـ Master List ---
# سنحاول البحث عن الملف في المسار الرئيسي
MASTER_FILE = "master_list.xlsx"

@st.cache_data
def load_master_data(file_path):
    try:
        m_df = pd.read_excel(file_path)
        m_df.columns = m_df.columns.astype(str).str.strip()
        return m_df
    except Exception as e:
        return None

master_df = load_master_data(MASTER_FILE)

if master_df is None:
    st.error(f"❌ لم يتم العثور على ملف {MASTER_FILE} في المجلد الرئيسي.")
    st.info("تأكد من رفع ملف الأسعار بنفس هذا الاسم إلى المستودع (GitHub) أو مجلد المشروع.")
    st.stop() # توقف هنا حتى يتم توفير الملف
else:
    st.sidebar.success("✅ تم تحميل قائمة الأسعار بنجاح")

# --- 2. رفع ملف العميل ---
uploaded_file = st.file_uploader("Upload Quotation File (Client)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.astype(str).str.strip()

        st.subheader("⚙️ إعدادات الربط والأسعار")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            client_item_col = st.selectbox("عمود اسم الدواء (عندك):", df.columns)
        with col2:
            master_item_col = st.selectbox("عمود اسم الدواء (في الأسعار):", master_df.columns)
        with col3:
            master_price_col = st.selectbox("عمود السعر (في الأسعار):", master_df.columns)

        if st.button("🚀 تشغيل التسعير الذكي"):
            # دالة للمطابقة الذكية لأسماء الأدوية
            def get_closest_match(name, choices):
                match = difflib.get_close_matches(str(name), choices, n=1, cutoff=0.6)
                return match[0] if match else None

            with st.spinner('جاري مطابقة الأسماء وجلب الأسعار...'):
                master_names = master_df[master_item_col].astype(str).tolist()
                
                # إنشاء عمود جديد للمطابقة
                df['Matched_Name'] = df[client_item_col].apply(lambda x: get_closest_match(x, master_names))
                
                # دمج البيانات لجلب السعر
                final_df = pd.merge(
                    df, 
                    master_df[[master_item_col, master_price_col]], 
                    left_on='Matched_Name', 
                    right_on=master_item_col, 
                    how='left'
                )

                # تخمين عمود الكمية
                qty_col = next((c for c in df.columns if 'qty' in c.lower() or 'quant' in c.lower()), None)
                if not qty_col:
                    qty_col = st.warning("لم يتم العثور على عمود الكمية تلقائياً، يرجى التأكد من تسميته بشكل صحيح.")
                else:
                    final_df[qty_col] = pd.to_numeric(final_df[qty_col], errors='coerce').fillna(0)
                    final_df[master_price_col] = pd.to_numeric(final_df[master_price_col], errors='coerce').fillna(0)
                    
                    # العملية الحسابية
                    final_df["Subtotal"] = final_df[qty_col] * final_df[master_price_col]
                    
                    st.success("✅ تمت العملية بنجاح!")
                    st.dataframe(final_df)
                    
                    total = final_df["Subtotal"].sum()
                    st.metric("إجمالي عرض السعر", f"{total:,.2f} EGP")

    except Exception as e:
        st.error(f"حدث خطأ فني: {e}")
