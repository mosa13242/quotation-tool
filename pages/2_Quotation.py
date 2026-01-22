import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Smart Quotation", layout="wide")
st.title("💰 نظام التسعير الدقيق")

MASTER_FILE = "master_list.xlsx"

if not os.path.exists(MASTER_FILE):
    st.error("❌ ملف الأسعار غير موجود.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = master_df.columns.astype(str).str.strip()

uploaded_file = st.file_uploader("ارفع ملف طلب العميل", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = df_client.columns.astype(str).str.strip()

    col1, col2 = st.columns(2)
    with col1:
        client_item_col = st.selectbox("عمود الصنف في ملفك:", df_client.columns)
        client_qty_col = st.selectbox("عمود الكمية في ملفك:", df_client.columns)
    with col2:
        master_item_col = st.selectbox("عمود الصنف في الماستر:", master_df.columns)
        master_price_col = st.selectbox("عمود السعر في الماستر:", master_df.columns)

    # إضافة خيار للتحكم في نوع المطابقة
    match_type = st.radio("نوع المطابقة:", ["تطابق تام (كلمة بكلمة)", "تطابق ذكي (دقة عالية جداً)"])

    if st.button("🚀 تنفيذ التسعير"):
        with st.spinner('جاري التسعير...'):
            
            # تنظيف البيانات قبل المقارنة
            df_client[client_item_col] = df_client[client_item_col].astype(str).str.strip()
            master_df[master_item_col] = master_df[master_item_col].astype(str).str.strip()

            if match_type == "تطابق تام (كلمة بكلمة)":
                # الربط فقط إذا كانت الكلمة مطابقة تماماً
                final_df = pd.merge(
                    df_client, 
                    master_df[[master_item_col, master_price_col]], 
                    left_on=client_item_col, 
                    right_on=master_item_col, 
                    how='left'
                )
            else:
                # مطابقة ذكية لكن بشرط دقة 90% على الأقل لمنع ربط كلمات عشوائية
                import difflib
                def strict_match(name, choices):
                    m = difflib.get_close_matches(str(name), choices, n=1, cutoff=0.9)
                    return m[0] if m else None
                
                master_names = master_df[master_item_col].unique().tolist()
                df_client['Matched_Name'] = df_client[client_item_col].apply(lambda x: strict_match(x, master_names))
                
                final_df = pd.merge(
                    df_client, 
                    master_df[[master_item_col, master_price_col]], 
                    left_on='Matched_Name', 
                    right_on=master_item_col, 
                    how='left'
                )

            # تحويل القيم لأرقام وحساب الإجمالي
            final_df[client_qty_col] = pd.to_numeric(final_df[client_qty_col], errors='coerce').fillna(0)
            final_df[master_price_col] = pd.to_numeric(final_df[master_price_col], errors='coerce').fillna(0)
            final_df["Total"] = final_df[client_qty_col] * final_df[master_price_col]
            
            st.dataframe(final_df)
            st.metric("الإجمالي", f"{final_df['Total'].sum():,.2f} EGP")
