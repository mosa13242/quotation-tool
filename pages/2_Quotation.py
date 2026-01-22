import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz

st.set_page_config(page_title="Quotation", layout="wide")

MASTER_FILE = "master_list.xlsx"

# =========================
# تحميل / إنشاء الماستر
# =========================
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df

master_df = load_master()
master_names = master_df["Item"].astype(str).tolist()
price_lookup = dict(zip(master_df["Item"], master_df["Price"]))

st.title("📄 Quotation & Pricing")

# =========================
# رفع ملف العميل
# =========================
uploaded_file = st.file_uploader("📤 ارفع ملف طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]

    st.subheader("⚙️ ربط الأعمدة")

    col1, col2 = st.columns(2)
    with col1:
        item_col = st.selectbox("عمود الصنف", df.columns)
        qty_col = st.selectbox("عمود الكمية", df.columns)

    with col2:
        st.write("الماستر ثابت:")
        st.code("Item | Price")

    # =========================
    # تنفيذ البحث والتسعير
    # =========================
    if st.button("🔍 تنفيذ البحث والتسعير"):
        def smart_match(text):
            if not master_names:
                return text
            match, score = process.extractOne(
                str(text), master_names, scorer=fuzz.token_set_ratio
            )
            return match if score >= 70 else text

        df["REMARKS"] = df[item_col].astype(str).apply(smart_match)
        df["Unit_Price"] = df["REMARKS"].map(price_lookup).fillna(0.0)

        st.session_state["quote_df"] = df

    # =========================
    # جدول التعديل
    # =========================
    if "quote_df" in st.session_state:
        st.info("✏️ عدّل الاسم أو السعر مباشرة في الجدول")

        edited_df = st.data_editor(
            st.session_state["quote_df"],
            use_container_width=True,
            num_rows="fixed"
        )

        # =========================
        # حفظ + حساب
        # =========================
        if st.button("💾 اعتماد وحفظ"):
            master_df = load_master()
            master_items = master_df["Item"].astype(str).tolist()
            new_rows = []

            for _, row in edited_df.iterrows():
                name = str(row["REMARKS"]).strip()
                price = float(row["Unit_Price"])

                if name and name not in master_items:
                    new_rows.append({
                        "Item": name,
                        "Price": price
                    })
                    master_items.append(name)

            if new_rows:
                master_df = pd.concat(
                    [master_df, pd.DataFrame(new_rows)],
                    ignore_index=True
                )
                master_df.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_rows)} صنف جديد للماستر")

            # الحساب النهائي
            edited_df[qty_col] = pd.to_numeric(
                edited_df[qty_col], errors="coerce"
            ).fillna(0)

            edited_df["Total"] = edited_df[qty_col] * edited_df["Unit_Price"]

            st.subheader("📊 النتيجة النهائية")
            st.dataframe(edited_df, use_container_width=True)

            st.metric(
                "💰 الإجمالي",
                f"{edited_df['Total'].sum():,.2f}"
            )


