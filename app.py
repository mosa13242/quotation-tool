import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="نظام التسعير المتكامل", layout="wide")

st.title("👋 أهلاً بك في نظام إدارة الأسعار")
st.write("استخدم القائمة الجانبية للتحكم في الماستر لست أو لتسعير طلبات العملاء.")

# إنشاء ملف الماستر إذا لم يكن موجوداً
if not os.path.exists("master_list.xlsx"):
    df = pd.DataFrame(columns=["Item", "Price"])
    df.to_excel("master_list.xlsx", index=False)
    st.info("تم إنشاء ملف master_list.xlsx جديد.")
