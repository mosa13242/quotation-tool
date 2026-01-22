import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="نظام إدارة الماستر", layout="wide")

# كود إجباري لإنشاء ملف الماستر في أول تشغيل
if not os.path.exists("master_list.xlsx"):
    df_init = pd.DataFrame(columns=["Item", "Price"])
    df_init.to_excel("master_list.xlsx", index=False)
    st.success("✅ تم إنشاء ملف الماستر (master_list.xlsx) بنجاح في مجلد المشروع.")

st.title("🛡️ نظام إدارة التسعير")
st.write("ملف الماستر جاهز الآن. يمكنك إدارته من القائمة الجانبية.")
