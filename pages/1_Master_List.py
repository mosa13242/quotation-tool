import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Master List", layout="wide")

# =========================
# Paths
# =========================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MASTER_FILE = DATA_DIR / "master_list.csv"

# =========================
# Helpers
# =========================
def load_master():
    if MASTER_FILE.exists():
        return pd.read_csv(MASTER_FILE)
    return pd.DataFrame(columns=["Item", "Unit_Price"])

def save_master(df: pd.DataFrame):
    df.to_csv(MASTER_FILE, index=False)

def normalize_cols(df):
    df.columns = [c.strip() for c in df.columns]
    return df

# =========================
# UI
# =========================
st.title("📦 Master List")

base_df = load_master()

uploaded = st.file_uploader(
    "ارفع ملف Excel",
    type=["xlsx", "xls"]
)

if uploaded:
    df_xl = pd.read_excel(uploaded)
    df_xl = normalize_cols(df_xl)

    st.subheader("اختيار الأعمدة")
    col_item = st.selectbox("عمود الصنف", df_xl.columns)
    col_price = st.selectbox("عمود السعر", df_xl.columns)

    merge = st.checkbox("تحديث السعر لو الصنف موجود", value=True)

    if st.button("➕ إضافة إلى قاعدة البيانات"):
        new_df = df_xl[[col_item, col_price]].copy()
        new_df.columns = ["Item", "Unit_Price"]

        if merge and not base_df.empty:
            merged = base_df.set_index("Item")
            new_df = new_df.set_index("Item")
            merged.update(new_df)
            merged = pd.concat([merged, new_df[~new_df.index.isin(merged.index)]])
            result = merged.reset_index()
        else:
            result = pd.concat([base_df, new_df], ignore_index=True)

        result["Unit_Price"] = pd.to_numeric(result["Unit_Price"], errors="coerce").fillna(0)
        save_master(result)

        st.success("✅ تم إضافة البيانات بنجاح")
        st.rerun()

# =========================
# Editor
# =========================
st.subheader("✏️ تعديل البيانات")

master_df = load_master()

edited_df = st.data_editor(
    master_df,
    column_config={
        "Item": st.column_config.TextColumn(label="الصنف"),
        "Unit_Price": st.column_config.NumberColumn(
            label="سعر الوحدة",
            min_value=0.0,
            format="%.2f"
        ),
    },
    use_container_width=True
)

if st.button("💾 حفظ التعديلات"):
    save_master(edited_df)
    st.success("تم الحفظ")


