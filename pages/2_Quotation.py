import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz

st.set_page_config(page_title="Quotation", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ================= تحميل الماستر =================
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df

    df = pd.read_excel(MASTER_FILE)
    df.columns = df.columns.str.strip()
    return df


master_df = load_master()
master_items = master_df["Item"].astype(str).tolist()

st.title("📄 نظام التسعير")

# ================= رفع ملف العميل =================
uploaded_file = st.file_uploader("📤 ارفع ملف العميل", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    st.subheader("⚙️ ربط الأعمدة")

    c1, c2 = st.columns(2)
    with c1:
        item_col = st.selectbox("عمود الصنف (العميل)", df.columns)
        qty_col = st.selectbox("عمود الكمية", df.columns)

    with c2:
        price_col = st.selectbox("عمود السعر (الماستر)", master_df.columns)

    # ================= البحث الذكي =================
    if st.button("🔍 تنفيذ البحث"):
        def smart_find(text):
            if not master_items:
                return "", 0

            match, score = process.extractOne(
                str(text),
                master_items,
                scorer=fuzz.token_set_ratio
            )
            return match if score >= 70 else "", score

        remarks = []
        prices = []

        for val in df[item_col]:
            match, score = smart_find(val)
            if match:
                price = master_df.loc[
                    master_df["Item"] == match, price_col
                ].values[0]
            else:
                price = 0

            remarks.append(match if match else val)
            prices.append(price)

        df["REMARKS"] = remarks
        df["Unit_Price"] = prices

        st.session_state["df"] = df.copy()

    # ================= جدول التعديل =================
    if "df" in st.session_state:
        st.info("✍️ عدّل REMARKS أو السعر يدويًا لو حابب")

        edited_df = st.data_editor(
            st.session_state["df"],
            use_container_width=True,
            key="editor"
        )

        # ================= حفظ =================
        if st.button("💾 اعتماد وحفظ"):
            master_df = load_master()
            existing = master_df["Item"].astype(str).tolist()

            new_rows = []

            for _, row in edited_df.iterrows():
                name = str(row["REMARKS"]).strip()
                price = float(row["Unit_Price"])

                if name and name not in existing:
                    new_rows.append({
                        "Item": name,
                        price_col: price
                    })
                    existing.append(name)

            if new_rows:
                master_df = pd.concat(
                    [master_df, pd.DataFrame(new_rows)],
                    ignore_index=True
                )
                master_df.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_rows)} صنف جديد")

            edited_df[qty_col] = pd.to_numeric(
                edited_df[qty_col],
                errors="coerce"
            ).fillna(0)

            edited_df["Total"] = (
                edited_df[qty_col] * edited_df["Unit_Price"]
            )

            st.subheader("📊 النتيجة النهائية")
            st.dataframe(edited_df, use_container_width=True)
            st.metric("💰 الإجمالي", f"{edited_df['Total'].sum():,.2f}")


