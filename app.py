import streamlit as st
import pandas as pd
import os
from thefuzz import process

# ---------------- SETTINGS ----------------
st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ---------------- LOAD MASTER ----------------
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]

    if "Item" not in df.columns or "Price" not in df.columns:
        st.error("❌ Master List لازم يحتوي على Item و Price")
        st.stop()

    return df

master_df = load_master()
master_items = master_df["Item"].astype(str).tolist()

# ---------------- TITLE ----------------
st.title("📋 Quotation Tool")

uploaded = st.file_uploader("📤 ارفع ملف الطلب", type=["xlsx"])

if uploaded:

    req_df = pd.read_excel(uploaded)
    req_df.columns = [c.strip() for c in req_df.columns]

    if "Item" not in req_df.columns:
        st.error("❌ ملف الطلب لازم يحتوي عمود Item")
        st.stop()

    st.subheader("🔎 تنفيذ المطابقة الذكية")

    results = []

    for item in req_df["Item"]:

        match, score = process.extractOne(item, master_items)

        price_row = master_df[master_df["Item"] == match]

        price = price_row["Price"].values[0] if not price_row.empty else 0

        results.append({
            "Requested Item": item,
            "Matched Item": match,
            "Match Score": score,
            "Quantity": 1,
            "Price": price,
            "Remarks": match
        })

    result_df = pd.DataFrame(results)

    st.subheader("📊 نتائج المطابقة")

    edited_df = st.data_editor(
        result_df,
        column_config={
            "Matched Item": st.column_config.SelectboxColumn(
                "Matched Item",
                options=master_items,
                required=True
            ),
            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=1,
                step=1
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # ---------------- UPDATE PRICE WHEN ITEM CHANGES ----------------
    for i, row in edited_df.iterrows():
        price_row = master_df[master_df["Item"] == row["Matched Item"]]
        if not price_row.empty:
            edited_df.at[i, "Price"] = price_row["Price"].values[0]
            edited_df.at[i, "Remarks"] = row["Matched Item"]

    st.subheader("⬇️ تحميل ملف التسعير")

    output_file = "quotation_result.xlsx"
    edited_df.to_excel(output_file, index=False)

    with open(output_file, "rb") as f:
        st.download_button(
            "تحميل Excel النهائي",
            f,
            file_name="quotation_result.xlsx"
        )
