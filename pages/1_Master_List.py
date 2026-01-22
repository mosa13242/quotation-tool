import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Master List", layout="wide")
st.title("📦 Master List")

# =========================
# المسارات
# =========================
DATA_DIR = "data"
MASTER_PATH = os.path.join(DATA_DIR, "master_list.xlsx")

# =========================
# إنشاء فولدر data لو مش موجود
# =========================
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# تحميل أو إنشاء ملف الماستر
# =========================
if not os.path.exists(MASTER_PATH):
    df_master = pd.DataFrame(columns=["Item", "Unit_Price"])
    df_master.to_excel(MASTER_PATH, index=False)
else:
    df_master = pd.read_excel(MASTER_PATH)

# =========================
# تأكيد الأعمدة
# =========================
required_cols = {"Item", "Unit_Price"}
if not required_cols.issubset(df_master.columns):
    st.error("❌ ملف الماستر يجب أن يحتوي على الأعمدة: Item | Unit_Price")
    st.stop()

# =========================
# تنظيف البيانات
# =========================
df_master["Item"] = df_master["Item"].astype(str).str.strip()
df_master["Unit_Price"] = pd.to_numeric(
    df_master["Unit_Price"], errors="coerce"
).fillna(0)

# =========================
# عرض وتعديل البيانات
# =========================
st.subheader("✏️ تعديل الأصناف والأسعار")

edited_df = st.data_editor(
    df_master,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Item": st.column_config.TextColumn("الصنف"),
        "Unit_Price": st.column_config.NumberColumn(
            "سعر الوحدة",
            min_value=0.0,
            format="%.2f"
        )
    }
)

# =========================
# حفظ
# =========================
if st.button("💾 حفظ الماستر"):
    edited_df.to_excel(MASTER_PATH, index=False)
    st.success("✅ تم حفظ الماستر بنجاح")


