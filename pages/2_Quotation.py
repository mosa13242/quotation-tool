import streamlit as st
import pandas as pd
import os
from pdf2image import convert_from_bytes
import pytesseract
import numpy as np
from PIL import Image

st.set_page_config(page_title="نظام التسعير بالذكاء الاصطناعي", layout="wide")

# 1. تحميل الماستر ليست (معالجة أخطاء التسمية)
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    st.error("❌ ارفع ملف الأسعار أولاً في صفحة Master List.")
    st.stop()

master_df = pd.read_excel(MASTER_FILE)
master_df.columns = [str(c).strip() for c in master_df.columns]

st.title("📸 تسعير ملفات الصور والـ PDF")

uploaded_file = st.file_uploader("ارفع طلب العميل (صور أو PDF ممسوح)", type=["xlsx", "pdf", "png", "jpg"])

if uploaded_file:
    df_client = pd.DataFrame()

    if uploaded_file.name.lower().endswith(('.pdf', '.png', '.jpg')):
        with st.spinner("🔍 جاري تحليل الصورة واستخراج النصوص..."):
            try:
                # إذا كان PDF نحوله لصور أولاً
                if uploaded_file.name.lower().endswith('.pdf'):
                    images = convert_from_bytes(uploaded_file.read())
                else:
                    images = [Image.open(uploaded_file)]

                all_text = ""
                for img in images:
                    # تحويل الصورة لنص (يدعم العربية والإنجليزية)
                    text = pytesseract.image_to_string(img, lang='eng+ara')
                    all_text += text + "\n"
                
                # تحويل النص المستخرج إلى جدول بسيط (تجريبي)
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                df_client = pd.DataFrame(lines, columns=["Extracted_Text"])
                st.info("💡 تم استخراج النصوص. اختر العمود الذي يحتوي على اسم الصنف.")
            except Exception as e:
                st.error(f"حدث خطأ في قراءة الصورة: {e}")
    
    elif uploaded_file.name.lower().endswith('.xlsx'):
        df_client = pd.read_excel(uploaded_file)

    if not df_client.empty:
        df_client.columns = [str(c).strip() for c in df_client.columns]
        
        # إعدادات الربط
        st.subheader("⚙️ إعدادات المطابقة")
        c1, c2 = st.columns(2)
        with c1:
            item_col = st.selectbox("عمود الصنف المستخرج:", df_client.columns)
            qty_col = st.number_input("الكمية الافتراضية (لأن الصور قد لا تقرأ الأرقام بدقة):", value=1)
        with c2:
            m_item = st.selectbox("عمود الصنف في الماستر:", master_df.columns)
            m_price = st.selectbox("عمود السعر في الماستر:", master_df.columns)

        if st.button("🚀 تسعير البيانات المستخرجة"):
            # تنظيف البيانات لضمان تطابق تام (Exact Match)
            # تم إلغاء المطابقة المرنة لمنع أخطاء مثل Television
            price_map = dict(zip(master_df[m_item].astype(str).str.strip(), master_df[m_price]))
            
            df_client['Matched_Price'] = df_client[item_col].astype(str).str.strip().map(price_map)
            df_client['Matched_Price'] = pd.to_numeric(df_client['Matched_Price'], errors='coerce').fillna(0)
            df_client['Total'] = qty_col * df_client['Matched_Price']
            
            # إخفاء الصفوف التي لم يتم العثور على سعر لها لتقليل الفوضى
            final_display = df_client[df_client['Matched_Price'] > 0]
            
            if not final_display.empty:
                st.success(f"✅ تم العثور على {len(final_display)} صنف مطابق.")
                st.dataframe(final_display, use_container_width=True)
                st.metric("الإجمالي", f"{final_display['Total'].sum():,.2f} EGP")
            else:
                st.warning("⚠️ لم يتم العثور على تطابق تام. تأكد أن الأسماء في الصورة مطابقة تماماً للماستر ليست.")
