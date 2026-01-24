import streamlit as st
import pandas as pd
import os
import io
from thefuzz import process, fuzz

st.set_page_config(page_title="Quotation", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ----------------------------
# LOAD MASTER
# ----------------------------
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df


master_df = load_master()
master_items = master_df["Item"].astype(str).tolist()

# ----------------------------
# SESSION
# ----------------------------
if "result_df" not in st.session_state:
    st.session_state.result_df = None

# ----------------------------
# UI
# ----------------------------
st.title("📋 نتائج المطابقة")

col1, col2 = st.columns(2)

with col1:
    item_col = st.selectbox("عمود الصنف", master_df.columns)

with col2:
    qty_col = st.selectbox("عمود الكمية", ["Quantity"])

# ----------------------------
# FUZZY MATCH
# ----------------------------
if st.button("🔍 تنفيذ المطابقة الذكية"):

    uploaded = st.file_uploader("ارفع ملف الطلب", type=["xlsx"])

    if uploaded:
        req_df = pd.read_excel(uploaded)

        results = []

        for _, row in req_df.iterrows():
            req_item = str(row[item_col])

            match, score = process.extractOne(
                req_item,
                master_items,
                scorer=fuzz.token_sort_ratio,
            )

            price = master_df.loc[
                master_df["Item"] == match, "Price"
            ].values

            price = price[0] if len(price) else 0

            results.append(
                {
                    "Requested Item": req_item,
                    "Matched Item": match,
                    "Match Score": score,
                    "Quantity": row.get(qty_col, 1),
                    "Price": price,
                    "Remarks": "",
                    "Confirm": False,
                }
            )

        st.session_state.result_df = pd.DataFrame(results)

# ----------------------------
# DISPLAY + EDIT
# ----------------------------
if st.session_state.result_df is not None:

    st.subheader("📊 النتائج")

    edited_df = st.data_editor(
        st.session_state.result_df,
        num_rows="fixed",
        column_config={
            "Matched Item": st.column_config.SelectboxColumn(
                "Matched Item",
                options=master_items,
            ),
            "Confirm": st.column_config.CheckboxColumn(),
        },
        use_container_width=True,
        key="editor",
    )

    # ----------------------------
    # AUTOFILL PRICE
    # ----------------------------
    for i, row in edited_df.iterrows():
        item = row["Matched Item"]
        price = master_df.loc[
            master_df["Item"] == item, "Price"
        ].values

        if len(price):
            edited_df.at[i, "Price"] = price[0]

    st.session_state.result_df = edited_df

    # ----------------------------
    # DOWNLOAD
    # ----------------------------
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited_df.to_excel(writer, index=False)

    buffer.seek(0)

    st.download_button(
        "⬇ تحميل النتيجة",
        buffer,
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
