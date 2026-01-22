import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quotation", layout="wide")

st.title("📄 صفحة التسعير")

# =========================
# رفع ملف طلب العميل
# =========================
uploaded_file = st.file_uploader(
    "📤 ارفع ملف طلب العميل (Excel)",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("⬆️ من فضلك ارفع ملف Excel")
    st.stop()

# =========================
# منع استخدام ملف الماستر
# =========================
file_name = uploaded_file.name.lower()
if "master" in file_name:
    st.error("❌ هذا ملف الماستر (Master List) ولا يمكن استخدامه في صفحة التسعير")
    st.stop()

# =========================
# قراءة ملف العميل
# =========================
try:
    customer_df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error("❌ خطأ في قراءة ملف الإكسيل")
    st.stop()

# =========================
# التحقق من الأعمدة
# =========================
required_columns = ["Item", "Quantity"]
missing = [c for c in required_columns if c not in customer_df.columns]

if missing:
    st.error(f"❌ الملف ناقص الأعمدة التالية: {', '.join(missing)}")
    st.stop()

st.success("✅ تم رفع ملف طلب العميل بنجاح")

# =========================
# تحميل الماستر
# =========================
MASTER_PATH = "data/master_list.xlsx"



