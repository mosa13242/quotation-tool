import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="نظام التسعير المتكامل", layout="wide")

st.title("🛡️ نظام إدارة التسعير والماستر")
st.write("أهلاً بك. استخدم القائمة الجانبية للتنقل بين إدارة الماستر وتسعير الطلبات.")

# إنشاء ملف الماستر إذا لم يكن موجوداً لضمان عدم حدوث خطأ
if not os.path.exists("master_list.xlsx"):
    df_init = pd.DataFrame(columns=["Item", "Price"])
    df_init.to_excel("master_list.xlsx", index=False)
    st.info("تم إنشاء ملف master_list.xlsx تلقائياً.")




