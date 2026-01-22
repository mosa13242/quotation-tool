import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="Quotation", layout="wide")

MASTER_FILE = "master_list.xlsx"


# =========================
# Master helpers
# =========================
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Unit_Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df
    return pd.read_excel(MASTER_FILE)


def save_master(df):
    df.to_excel(MASTER_FILE, index=False)


master_df = load_master()
master_names = master_df["Item"].astype(str).tolist() if not master_df.empty else []


# =========================
# UI
# =========================
st.title("🧾 صفحة التسعير")

uploaded_file = st.file_uploader("📤 ارفع ملف طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]

    col1, col2 = st.columns(2)
    with col1:
        c_item = st.selectbox("عمود الصنف", df_client.columns)
        c_qty = st.selectbox("عمود الكمية", df_client.columns)
    with col2:
        st.info("سيتم التسعير حسب الماستر أو يدويًا")

    # =========================
    # Smart matching
    # =========================
    def smart_match(text):
        if not master_names:
            return str(text)
        match, score = process.extractOne(
            str(text), master_names, scorer=fuzz.token_set_ratio
        )
        return match if score >= 70 else str(text)

    if st.button("🔍 مطابقة الأصناف"):
        df_client["REMARKS"] = df_client[c_item].apply(smart_match)
        price_map = dict(zip(master_df["Item"], master_df["Unit_Price"]))
        df_client["Unit_Price"] = df_client["REMARKS"].map(price_map).fillna(0.0)
        st.session_state["df_work"] = df_client.copy()

# =========================
# Editor
# =========================
if "df_work" in st.session_state:
    st.subheader("✏️ التعديل النهائي")

    edited_df = st.data_editor(
        st.session_state["df_work"],
        column_config={
            "REMARKS": st.column_config.TextColumn(
                "الصنف",
                suggestions=master_names,
                width="large",
            ),
            "Unit_Price": st.column_config.NumberColumn(
                "سعر الوحدة",
                min_value=0.0,
                format="%.2f",
            ),
        },
        disabled=[c_item, c_qty],
        use_container_width=True,
    )

    # =========================
    # Calculations
    # =========================
    edited_df[c_qty] = pd.to_numeric(
        edited_df[c_qty], errors="coerce"
    ).fillna(0)
    edited_df["Unit_Price"] = pd.to_numeric(
        edited_df["Unit_Price"], errors="coerce"
    ).fillna(0)

    edited_df["Total"] = edited_df[c_qty] * edited_df["Unit_Price"]

    # =========================
    # Save to master
    # =========================
    if st.button("🚀 اعتماد وحفظ الأسعار في الماستر"):
        master_df = load_master()
        existing_items = master_df["Item"].astype(str).tolist()

        for _, row in edited_df.iterrows():
            item = str(row["REMARKS"]).strip()
            price = float(row["Unit_Price"])

            if item == "":
                continue

            if item in existing_items:
                master_df.loc[
                    master_df["Item"] == item, "Unit_Price"
                ] = price
            else:
                master_df = pd.concat(
                    [
                        master_df,
                        pd.DataFrame(
                            [{"Item": item, "Unit_Price": price}]
                        ),
                    ],
                    ignore_index=True,
                )

        save_master(master_df)
        st.success("✅ تم حفظ الأسعار في الماستر")

    # =========================
    # Result
    # =========================
    st.subheader("📊 النتيجة النهائية")
    st.dataframe(edited_df, use_container_width=True)

    total_sum = edited_df["Total"].sum()
    st.metric("💰 الإجمالي الكلي", f"{total_sum:,.2f}")


