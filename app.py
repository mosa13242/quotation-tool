import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz

# ================== إعداد الصفحة ==================
st.set_page_config(page_title="Quotation System", layout="wide")
st.title("📊 نظام التسعير والـ Quotation")

MASTER_FILE = "master_list.xlsx"

# ================== تحميل / إنشاء الماستر ==================
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Unit_Price"])
        df.to_excel(MASTER_FILE, index=False)
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    names = df["Item"].astype(str).tolist()
    return df, names

master_df, master_names = load_master()

# ================== رفع ملف العميل ==================
uploaded_file = st.file_uploader("📂 ارفع ملف طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    client_df = pd.read_excel(uploaded_file)
    client_df.columns = [c.strip() for c in client_df.columns]

    st.subheader("⚙️ ربط الأعمدة")

    col1, col2 = st.columns(2)
    with col1:
        item_col = st.selectbox("عمود الصنف", client_df.columns)
        qty_col = st.selectbox("عمود الكمية", client_df.columns)

    # ================== البحث الذكي ==================
    def smart_match(text):
        if not master_names:
            return text
        match, score = process.extractOne(
            str(text), master_names, scorer=fuzz.token_set_ratio
        )
        return match if score >= 60 else text

    if st.button("🔍 مطابقة الأصناف من الماستر"):
        client_df["REMARKS"] = client_df[item_col].apply(smart_match)

        price_map = dict(
            zip(master_df["Item"], master_df["Unit_Price"])
        )

        client_df["Unit_Price"] = client_df["REMARKS"].map(price_map).fillna(0.0)

        st.session_state["df"] = client_df.copy()

    # ================== جدول التعديل ==================
    if "df" in st.session_state:
        st.subheader("✏️ تعديل الأصناف والأسعار")

        edited_df = st.data_editor(
            st.session_state["df"],
            use_container_width=True,
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث / إضافة)",
                    suggestions=master_names
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "سعر الوحدة",
                    min_value=0.0,
                    format="%.2f"
                )
            },
            disabled=[item_col],
            key="editor"
        )

        # ================== إعادة البحث بعد التعديل ==================
        if st.button("🔁 إعادة البحث في الماستر"):
            price_map = dict(
                zip(master_df["Item"], master_df["Unit_Price"])
            )

            edited_df["REMARKS"] = edited_df["REMARKS"].apply(smart_match)
            edited_df["Unit_Price"] = edited_df["REMARKS"].map(price_map).fillna(
                edited_df["Unit_Price"]
            )

            st.session_state["df"] = edited_df
            st.success("✅ تم تحديث الأسعار من الماستر")

        # ================== حفظ الجديد في الماستر ==================
        if st.button("💾 اعتماد وحفظ الأصناف الجديدة"):
            new_rows = []
            master_df, master_names = load_master()

            for _, row in edited_df.iterrows():
                name = str(row["REMARKS"]).strip()
                price = float(row["Unit_Price"])

                if name and name not in master_names:
                    new_rows.append(
                        {"Item": name, "Unit_Price": price}
                    )
                    master_names.append(name)

            if new_rows:
                master_df = pd.concat(
                    [master_df, pd.DataFrame(new_rows)],
                    ignore_index=True
                )
                master_df.to_excel(MASTER_FILE, index=False)
                st.success("✅ تم حفظ الأصناف الجديدة في الماستر")

        # ================== الحساب النهائي ==================
        edited_df[qty_col] = pd.to_numeric(
            edited_df[qty_col], errors="coerce"
        ).fillna(0)

        edited_df["Total"] = edited_df[qty_col] * edited_df["Unit_Price"]

        st.subheader("📈 النتيجة النهائية")
        st.dataframe(edited_df, use_container_width=True)

        st.metric(
            "💰 الإجمالي الكلي",
            f"{edited_df['Total'].sum():,.2f}"
        )



