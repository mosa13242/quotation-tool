import streamlit as st
import pandas as pd
import os
from thefuzz import process, fuzz

# ================== CONFIG ==================
st.set_page_config(page_title="Quotation System", layout="wide")
MASTER_FILE = "master_list.xlsx"

# ================== MASTER ==================
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Unit_Price"])
        df.to_excel(MASTER_FILE, index=False)
    df = pd.read_excel(MASTER_FILE)
    df["Item"] = df["Item"].astype(str).str.strip()
    return df

master_df = load_master()
master_names = master_df["Item"].tolist()

# ================== TITLE ==================
st.title("📦 Quotation & Pricing System")

# ================== UPLOAD CLIENT FILE ==================
uploaded = st.file_uploader("📤 ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded:
    client_df = pd.read_excel(uploaded)
    client_df.columns = [c.strip() for c in client_df.columns]

    st.subheader("🔧 ربط الأعمدة")

    c1, c2 = st.columns(2)
    with c1:
        item_col = st.selectbox("عمود الصنف (الطلب)", client_df.columns)
        qty_col = st.selectbox("عمود الكمية", client_df.columns)
    with c2:
        unit_col = st.selectbox("عمود الوحدة (اختياري)", client_df.columns)

    # ================== PREPARE DATA ==================
    if "df" not in st.session_state:
        df = client_df.copy()
        df["REMARKS"] = df[item_col].astype(str)
        df["Unit_Price"] = 0.0
        st.session_state.df = df

    st.subheader("✏️ التعديل والبحث")

    edited_df = st.data_editor(
        st.session_state.df,
        column_config={
            "REMARKS": st.column_config.TextColumn(
                "الصنف (بحث في الماستر)",
                suggestions=master_names,
                width="large",
            ),
            "Unit_Price": st.column_config.NumberColumn(
                "السعر",
                min_value=0.0,
                format="%.2f"
            ),
        },
        disabled=[item_col, qty_col, unit_col],
        use_container_width=True,
        key="editor"
    )

    # ================== SMART PRICING ==================
    def get_price(name, old_price):
        if not name or not master_names:
            return old_price
        match, score = process.extractOne(
            name, master_names, scorer=fuzz.token_set_ratio
        )
        if score >= 60:
            return float(
                master_df.loc[master_df["Item"] == match, "Unit_Price"].values[0]
            )
        return old_price

    if st.button("🔁 تسعير من الماستر"):
        prices = []
        names = []

        for _, r in edited_df.iterrows():
            price = get_price(r["REMARKS"], r["Unit_Price"])
            prices.append(price)
            names.append(r["REMARKS"])

        edited_df["Unit_Price"] = prices
        edited_df["REMARKS"] = names
        st.session_state.df = edited_df

        st.success("✅ تم التسعير من الماستر")

    # ================== SAVE NEW ITEMS ==================
    if st.button("💾 حفظ الأصناف الجديدة في الماستر"):
        new_rows = []
        for _, r in edited_df.iterrows():
            name = str(r["REMARKS"]).strip()
            price = float(r["Unit_Price"])
            if name and name not in master_names:
                new_rows.append({"Item": name, "Unit_Price": price})

        if new_rows:
            updated = pd.concat([master_df, pd.DataFrame(new_rows)], ignore_index=True)
            updated.to_excel(MASTER_FILE, index=False)
            st.success("✅ تم حفظ الأصناف الجديدة")
        else:
            st.info("ℹ️ لا يوجد أصناف جديدة")

    # ================== FINAL RESULT ==================
    edited_df[qty_col] = pd.to_numeric(
        edited_df[qty_col], errors="coerce"
    ).fillna(0)

    edited_df["Total"] = edited_df[qty_col] * edited_df["Unit_Price"]

    st.subheader("📊 النتيجة النهائية")
    st.dataframe(edited_df, use_container_width=True)

    st.metric(
        "💰 الإجمالي الكلي",
        f"{edited_df['Total'].sum():,.2f}"
    )




