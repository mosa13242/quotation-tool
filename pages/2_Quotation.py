import streamlit as st
import pandas as pd
import os
import re
from thefuzz import fuzz

MASTER_FILE = "master_list.xlsx"

# -----------------------------
# Load Master
# -----------------------------

@st.cache_data
def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["item", "price"])

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip().lower() for c in df.columns]

    return df


master_df = load_master()


# -----------------------------
# Cleaning
# -----------------------------

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------
# Word based matching
# -----------------------------

def token_match_score(a, b):

    a_tokens = set(clean_text(a).split())
    b_tokens = set(clean_text(b).split())

    if not a_tokens or not b_tokens:
        return 0

    common = a_tokens.intersection(b_tokens)

    return int((len(common) / len(a_tokens)) * 100)


def smart_match(item, master_items):

    best = None
    best_score = 0

    for m in master_items:
        score = token_match_score(item, m)

        if score > best_score:
            best_score = score
            best = m

    # ❗ حد أدنى صارم
    if best_score < 40:
        return None, best_score

    return best, best_score


# -----------------------------
# UI
# -----------------------------

st.title("Quotation Matching System")

uploaded = st.file_uploader("Upload Request File", type=["xlsx"])

if uploaded and not master_df.empty:

    req_df = pd.read_excel(uploaded)

    item_col = st.selectbox("Item column", req_df.columns)
    qty_col = st.selectbox("Quantity column", req_df.columns)

    if st.button("Run Matching"):

        results = []

        for _, row in req_df.iterrows():

            requested = row[item_col]
            qty = row[qty_col]

            matched, score = smart_match(
                requested,
                master_df["item"].tolist()
            )

            price = 0

            if matched:
                price = master_df.loc[
                    master_df["item"] == matched,
                    "price"
                ].values[0]

            results.append({
                "Requested Item": requested,
                "Matched Item": matched,
                "Match Score": score,
                "Quantity": qty,
                "Price": price,
                "Remarks": matched
            })

        result_df = pd.DataFrame(results)

        st.subheader("Results")

        # -----------------------------
        # 🔥 Editable with autocomplete
        # -----------------------------

        edited = st.data_editor(
            result_df,
            column_config={
                "Matched Item": st.column_config.SelectboxColumn(
                    "Matched Item",
                    options=master_df["item"].tolist()
                )
            },
            use_container_width=True
        )

        # recalc price if changed
        prices = []

        for _, r in edited.iterrows():

            if r["Matched Item"] in master_df["item"].values:
                p = master_df.loc[
                    master_df["item"] == r["Matched Item"],
                    "price"
                ].values[0]
            else:
                p = 0

            prices.append(p)

        edited["Price"] = prices

        import io

output = io.BytesIO()

with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    edited.to_excel(writer, index=False)

st.download_button(
    label="📥 تحميل ملف التسعير",
    data=output.getvalue(),
    file_name="quotation_result.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


elif master_df.empty:
    st.error("❌ Upload Master List first from Master List page")


