import streamlit as st
import pandas as pd
import os
import pdfplumber
import difflib

st.set_page_config(page_title="نظام التسعير النهائي", layout="wide")

# 1. تحميل قائمة الأسعار (Master List)
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف master_list.xlsx غير موجود.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("💰 نظام التسعير التلقائي (إصدار الحماية من الأخطاء)")

# 2. رفع ملف العميل
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel أو PDF)", type=["xlsx", "pdf"])

if uploaded_file:
    df_client = pd.DataFrame()
    if uploaded_file.name.endswith('.xlsx'):
        df_client = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.pdf'):
        with pdfplumber.open(uploaded_file) as pdf:
            all_rows = []
            for page in pdf.pages:
                table = page.extract_table()
                if table: all_rows.extend(table)
            if all_rows:
                df_client = pd.DataFrame(all_rows[1:], columns=all_rows[0])

    if not df_client.empty:
        df_client.columns = [str(c).strip() for c in df_client.columns]
        
        # --- واجهة اختيار الأعمدة ---
        st.subheader("⚙️ إعدادات الربط")
        c1, c2 = st.columns(2)
        with c1:
            client_item_col = st.selectbox("عمود الصنف (عندك):", df_client.columns)
            client_qty_col = st.selectbox("عمود الكمية (عندك):", df_client.columns)
        with c2:
            master_item_col = st.selectbox("عمود الصنف (في الماستر):", master_df.columns)
            master_price_col = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

        match_type = st.radio("نوع المطابقة:", ["تطابق تام (كلمة بكلمة)", "تطابق ذكي (دقة عالية)"])

        if st.button("🚀 تنفيذ التسعير"):
            # تنظيف البيانات
            df_client[client_item_col] = df_client[client_item_col].astype(str).str.strip()
            master_df[master_item_col] = master_df[master_item_col].astype(str).str.strip()

            # --- عملية الدمج الذكية ---
            if match_type == "تطابق تام (كلمة بكلمة)":
                # ندمج ونجلب فقط عمود السعر من الماستر ونعطيه اسماً فريداً فوراً
                final_df = df_client.copy()
                price_mapping = master_df.set_index(master_item_col)[master_price_col].to_dict()
                final_df['Target_Price'] = final_df[client_item_col].map(price_mapping)
            else:
                # مطابقة ذكية صارمة
                master_names = master_df[master_item_col].unique().tolist()
                def get_match(x):
                    m = difflib.get_close_matches(str(x), master_names, n=1, cutoff=0.9)
                    return m[0] if m else None
                
                df_client['Matched_Name'] = df_client[client_item_col].apply(get_match)
                final_df = pd.merge(df_client, master_df[[master_item_col, master_price_col]], 
                                    left_on='Matched_Name', right_on=master_item_col, how='left')
                # إعادة تسمية عمود السعر لضمان عدم حدوث KeyError
                final_df = final_df.rename(columns={master_price_col: 'Target_Price'})

            # --- الحسابات النهائية (باستخدام الاسم الجديد المضمون) ---
            final_df['Target_Price'] = pd.to_numeric(final_df['Target_Price'], errors='coerce').fillna(0)
            final_df[client_qty_col] = pd.to_numeric(final_df[client_qty_col], errors='coerce').fillna(0)
            
            final_df["Subtotal"] = final_df[client_qty_col] * final_df['Target_Price']
            
            st.success("✅ تمت العملية بنجاح دون أخطاء")
            st.dataframe(final_df)
            st.metric("إجمالي الفاتورة", f"{final_df['Subtotal'].sum():,.2f} EGP")
