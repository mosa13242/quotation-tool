import streamlit as st
import pandas as pd
import os
import re
from thefuzz import fuzz
import io

st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

def clean_col(c):
    return c.strip().lower().replace(" ", "").replace("_", "")

# ---------------------------------------------------
# -----------------------------
# Load Master
# ---------------------------------------------------
# -----------------------------

@st.cache_data
def load_master():
    df = pd.read_excel(MASTER_FILE)
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["item", "price"])

    rename_map = {}
    for c in df.columns:
        key = clean_col(c)
        if key == "item":
            rename_map[c] = "item"
        elif key == "price":
            rename_map[c] = "price"
        elif key in ["unitprice", "unit_price"]:
            rename_map[c] = "unit_price"

    df = df.rename(columns=rename_map)

    needed = {"item", "price"}
    if not needed.issubset(df.columns):
        st.error(f"❌ Master columns found: {list(df.columns)}")
        st.stop()

    if "unit_price" not in df.columns:
        df["unit_price"] = df["price"]
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip().lower() for c in df.columns]

    return df


master_df = load_master()
master_items = master_df["item"].astype(str).tolist()

# ---------------------------------------------------
# Cleaning
# ---------------------------------------------------

IGNORE_WORDS = {
    "mg","ml","tab","tablet","tablets","cap","capsule",
    "syrup","cream","solution","inj","amp","pcs","packet"
}
# -----------------------------
# Cleaning
# -----------------------------

def normalize(text):
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

    tokens = []
    for t in text.split():
        if t not in IGNORE_WORDS and not t.isdigit():
            tokens.append(t)

    return " ".join(tokens)
# -----------------------------
# Word based matching
# -----------------------------

def token_match_score(a, b):

master_df["norm"] = master_df["item"].apply(normalize)
    a_tokens = set(clean_text(a).split())
    b_tokens = set(clean_text(b).split())

# ---------------------------------------------------
# Matching
# ---------------------------------------------------
    if not a_tokens or not b_tokens:
        return 0

def smart_match(query):
    common = a_tokens.intersection(b_tokens)

    q_norm = normalize(query)

    best_row = None
    best_score = 0
    return int((len(common) / len(a_tokens)) * 100)

    for _, row in master_df.iterrows():

        m_norm = row["norm"]
def smart_match(item, master_items):

        q_words = set(q_norm.split())
        m_words = set(m_norm.split())

        if not q_words:
            continue

        overlap = len(q_words & m_words) / len(q_words)
        fuzzy = fuzz.token_set_ratio(q_norm, m_norm) / 100
    best = None
    best_score = 0

        score = overlap * 0.75 + fuzzy * 0.25
    for m in master_items:
        score = token_match_score(item, m)

        if score > best_score:
            best_score = score
            best_row = row
            best = m

    return best_row, round(best_score * 100)
    # ❗ حد أدنى صارم
    if best_score < 40:
        return None, best_score

    return best, best_score

# ---------------------------------------------------

# -----------------------------
# UI
# ---------------------------------------------------
# -----------------------------

st.title("📊 Quotation Tool")
st.title("Quotation Matching System")

uploaded = st.file_uploader("📄 ارفع ملف الطلب", type=["xlsx"])
uploaded = st.file_uploader("Upload Request File", type=["xlsx"])

if uploaded:
if uploaded and not master_df.empty:

    req_df = pd.read_excel(uploaded)

    req_df.columns = [c.strip() for c in req_df.columns]

    item_col = st.selectbox("عمود الصنف", req_df.columns)
    qty_col = st.selectbox("عمود الكمية", req_df.columns)

    if st.button("🔍 تنفيذ المطابقة"):

        rows = []

        for _, r in req_df.iterrows():

            req_item = str(r[item_col])
            qty = r[qty_col]

            match, score = smart_match(req_item)
    item_col = st.selectbox("Item column", req_df.columns)
    qty_col = st.selectbox("Quantity column", req_df.columns)

            if match is not None:
                rows.append({
                    "Requested Item": req_item,
                    "Matched Item": match["item"],
                    "Match Score": score,
                    "Quantity": qty,
                    "Price": match["price"],
                    "Remarks": match["item"]
                })
            else:
                rows.append({
                    "Requested Item": req_item,
                    "Matched Item": "",
                    "Match Score": 0,
                    "Quantity": qty,
                    "Price": 0,
                    "Remarks": ""
                })

        st.session_state["quotation"] = pd.DataFrame(rows)


# ---------------------------------------------------
# Results Table
# ---------------------------------------------------
    if st.button("Run Matching"):

if "quotation" in st.session_state:
        results = []

    df = st.session_state["quotation"]
        for _, row in req_df.iterrows():

    st.subheader("📋 Results")
            requested = row[item_col]
            qty = row[qty_col]

    edited = st.data_editor(
        df,
        column_config={
            "Matched Item": st.column_config.SelectboxColumn(
                options=master_items
            matched, score = smart_match(
                requested,
                master_df["item"].tolist()
            )
        },
        use_container_width=True
    )

    # update price after manual change
    for i, row in edited.iterrows():

        m = row["Matched Item"]

        price_row = master_df[master_df["item"] == m]
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

        if not price_row.empty:
            edited.loc[i, "Price"] = price_row["price"].values[0]
            prices.append(p)

    st.session_state["quotation"] = edited
        edited["Price"] = prices

    # ---------------------------------------------------
    # Export
    # ---------------------------------------------------
        st.download_button(
            "Download Quotation",
            edited.to_excel(index=False),
            file_name="quotation.xlsx"
        )

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited.to_excel(writer, index=False)
elif master_df.empty:
    st.error("❌ Upload Master List first from Master List page")

    st.download_button(
        "⬇ تحميل ملف التسعير",
        data=buffer.getvalue(),
        file_name="quotation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



