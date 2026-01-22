import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Master List", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ===============================
# تحميل / إنشاء ملف الماستر بأمان
# ===============================
def get_safe_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []

    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df["Item"].astype(str).tolist()
    return df, names


# ===============================
# واجهة الصفحة
# ===============================
st.title("📦 إضافة ملف Excel إلى قاعدة البيانات")

base_df, base_names = get_safe_master()

uploaded_file = st.file_uploader(
    "ارفع ملف Excel لإضافته إلى قاعدة البيانات",
    type=["xlsx"]
)

if uploaded_file:
    df_new = pd.read_excel(uploaded_file)
    df_new.columns = [str(c).strip() for c in df_new.columns]

    st.subheader("🔗 ربط الأعمدة")

    col1, col2 = st.columns(2)
    with col1:
        new_item_col = st.selectbox(
            "عمود الصنف في الملف الجديد",
            df_new.columns
        )
    with col2:
        new_price_col = st.selectbox(
            "عمود السعر في الملف الجديد",
            df_new.columns
        )

    update_existing = st.checkbox(
        "🔁 تحديث السعر إذا كان الصنف موجود بالفعل",
        value=True
    )

    if st.button("➕ دمج الملف مع قاعدة البيانات"):
        added = 0
        updated = 0

        for _, row in df_new.iterrows():
            item = str(row[new_item_col]).strip()
            try:
                price = float(row[new_price_col])
            except:
                price = 0.0

            if item == "" or item.lower() == "nan":
                continue

            if item in base_names:
                if update_existing:
                    base_df.loc[base_df["Item"] == item, "Price"] = price
                    updated += 1
            else:
                base_df = pd.concat(
                    [base_df, pd.DataFrame([{
                        "Item": item,
                        "Price": price
                    }])],
                    ignore_index=True
                )
                base_names.append(item)
                added += 1

        base_df.to_excel(MASTER_FILE, index=False)

        st.success(
            f"✅ تم الدمج بنجاح | تمت إضافة {added} صنف "
            f"| تم تحديث {updated} سعر"
        )

        st.subheader("📋 قاعدة البيانات الحالية")
        st.dataframe(base_df, use_container_width=True)

else:
    st.info("⬆️ ارفع ملف Excel للبدء")

