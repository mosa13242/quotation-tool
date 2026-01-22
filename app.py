import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="نظام التسعير الذكي", layout="wide")

MASTER_FILE = "master_list.xlsx"

# التأكد من وجود ملف الماستر عند التشغيل لأول مرة
if not os.path.exists(MASTER_FILE):
    df = pd.DataFrame(columns=["Item", "Price"])
    df.to_excel(MASTER_FILE, index=False)

st.title("🛡️ نظام إدارة التسعير المتكامل")
st.write("استخدم القائمة الجانبية للوصول إلى أدوات التسعير.")
