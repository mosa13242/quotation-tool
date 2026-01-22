import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="نظام إدارة التسعير", layout="wide")

# إنشاء ملف الماستر إذا لم يكن موجوداً
MASTER_FILE = "master_list.xlsx"
if not os.path.exists(MASTER_FILE):
    df = pd.DataFrame(columns=["Item", "Price"])
    df.to_excel(MASTER_FILE, index=False)

st.title("🚀 نظام التسعير المتكامل")
st.write("مرحباً بك. استخدم القائمة الجانبية للتنقل بين تحديث الماستر أو إصدار كوتيشن جديد.")

st.info("تأكد من رفع ملف الماستر أولاً في صفحة Master List ليبدأ النظام بالتعرف على الأصناف.")

