def get_safe_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).tolist()
    return df, names
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
