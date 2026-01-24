import streamlit as st
import pandas as pd
import os
import re
from rapidfuzz import process, fuzz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ---------------- CLEAN TEXT ----------------
def clean_text(txt):
    txt = str(txt).lower()
    txt = re.sub(r"\(.*?\)", "", txt)
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    txt = re.sub(r"\b(tab|tablet|cap|capsule|ml|mg|pcs|packet|bottle|vial)\b", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

# ---------------- LOAD MASTER ----------------
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]

    if "Item" not in df.columns or "Price" not in df.columns:
        st.error("❌ Master List لازم يحتوي Item و Price")
        st.stop()

    df["clean"] = df["Item"].apply(clean_text)

    return df

master_df = load_master()
master_items = master_df["Item"].tolist()
master_clean = master_df["clean"].tolist()

# ---------------- TITLE ----------------
st.title("📋 Smart Quotation Tool")

uploaded = st.file_uploader("📤 ارفع ملف الطلب", type=["xlsx"])

if uploaded:

    req_df = pd.read_excel(uploaded)
    req_df.columns = [c.strip() for c in req_df.columns]

    if "Item" not in req_df.columns:
        st.error("❌ ملف الطلب لازم يحتوي عمود Item")
        st.stop()

    st.subheader("🔍 Smart Matching")

    results = []

    for item in req_df["Item"]:

        cleaned = clean_text(item)

        matches = process.extract(
            cleaned,
            master_clean,
            scorer=fuzz.token_sort_ratio,
            limit=5
        )

        best_clean, score, idx = matches[0]
        best_item = master_df.iloc[idx]["Item"]
        price = master_df.iloc[idx]["Price"]

        results.append({
            "Requested Item": item,
            "Matched Item": best_item,
            "Match Score": score,
            "Quantity": 1,
            "Price": price,
            "Remarks": best_item
        })

    result_df = pd.DataFrame(results)

    st.subheader("📊 Results")

    edited_df = st.data_editor(
        result_df,
        column_config={
            "Matched Item": st.column_config.SelectboxColumn(
                "Matched Item",
                options=master_items
            ),
            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=1,
                step=1
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # ---------------- UPDATE PRICE ----------------
    for i, row in edited_df.iterrows():
        price_row = master_df[master_df["Item"] == row["Matched Item"]]
        if not price_row.empty:
            edited_df.at[i, "Price"] = price_row["Price"].values[0]
            edited_df.at[i, "Remarks"] = row["Matched Item"]

    # ---------------- DOWNLOAD ----------------
    st.subheader("⬇️ Download")

    out = "quotation_result.xlsx"
    edited_df.to_excel(out, index=False)

    with open(out, "rb") as f:
        st.download_button(
            "تحميل ملف التسعير",
            f,
            file_name="quotation_result.xlsx"
        )
