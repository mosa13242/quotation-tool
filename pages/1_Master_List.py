import streamlit as st
import pandas as pd

st.title("📋 إدارة قائمة الأسعار (Master List)")

try:
    df = pd.read_excel("master_list.xlsx")
    
    st.write("يمكنك تعديل الأسعار أو إضافة أصناف هنا مباشرة:")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="master_editor")
    
    if st.button("💾 حفظ التعديلات في الماستر"):
        edited_df.to_excel("master_list.xlsx", index=False)
        st.success("تم تحديث قائمة الماستر بنجاح!")
except Exception as e:
    st.error("تأكد من وجود ملف master_list.xlsx")
    st.divider()
st.header("📥 إضافة ملف Excel إلى قاعدة البيانات")

upload_master = st.file_uploader(
    "ارفع ملف Excel لإضافته إلى قاعدة البيانات",
    type=["xlsx"],
    key="upload_master_db"
)

if upload_master:
    df_new = pd.read_excel(upload_master)
    df_new.columns = [str(c).strip() for c in df_new.columns]

    col1, col2 = st.columns(2)
    with col1:
        new_item_col = st.selectbox("عمود الصنف", df_new.columns)
    with col2:
        new_price_col = st.selectbox("عمود السعر", df_new.columns)

    update_price = st.checkbox(
        "🔄 تحديث السعر إذا كان الصنف موجود بالفعل",
        value=True
    )

    if st.button("➕ دمج الملف مع قاعدة البيانات"):
        base_df, base_names = get_safe_master()

        df_new = df_new[[new_item_col, new_price_col]].copy()
        df_new.columns = ["Item", "Price"]

        df_new["Item"] = df_new["Item"].astype(str).str.strip()
        df_new["Price"] = pd.to_numeric(
            df_new["Price"], errors="coerce"
        ).fillna(0)

        for _, row in df_new.iterrows():
            item = row["Item"]
            price = row["Price"]

            if item in base_names:
                if update_price:
                    base_df.loc[
                        base_df["Item"] == item, "Price"
                    ] = price
            else:
                base_df.loc[len(base_df)] = [item, price]

        base_df.to_excel(MASTER_FILE, index=False)
        st.success("✅ تم دمج الملف بنجاح مع قاعدة البيانات")

