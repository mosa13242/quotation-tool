import streamlit as st
import pandas as pd
import re
from thefuzz import process, fuzz
import io

st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ----------------------------
# Load Master
# ----------------------------

@st.cache_data
def load_master():
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"item", "price", "unit_price"}
    if not required.issubset(df.columns):
        st.error(f"❌ Master must contain columns: {required}")
        st.stop()

    return df


master_df = load_master()
master_items = master_df["item"].astype(str).tolist()

# ----------------------------
# Cleaning
# ----------------------------

IGNORE_WORDS = {
    "mg","ml","tab","tabs","tablet","tablets","syrup","cream",
    "cap","capsule","amp","ampoule","vial","inj","solution",
    "pcs","packet","bottle","drop","drops"
}

def normalize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)

    tokens = []
    for t in text.split():
        if t not in IGNORE_WORDS and not t.isdigit():
            tokens.append(t)

    return " ".join(tokens)

master_df["norm"] = master_df["item"].apply(normalize)

# ----------------------------
# Matching Engine
# ----------------------------

def smart_match(query):
    q_norm = normalize(query)

    # exact word overlap score
    best = None
    best_score = 0

    for _, row in master_df.iterrows():
        m_norm = row["norm"]

        q_words = set(q_norm.split())
        m_words = set(m_norm.split())

        if not q_words:
            continue

        overlap = len(q_words & m_words) / len(q_words)

        fuzzy_score = fuzz.token_set_ratio(q_norm, m_norm) / 100

        score = overlap * 0.7 + fuzzy_score * 0.3

        if score > best_score:
            best_score = score
            best = row

    return best, round(best_score * 100)


# ----------------------------
# UI
# ----------------------------

st.title("📊 Quotation Tool")

uploaded = st.file_uploader("📄 ارفع ملف الطلب (Excel)", type=["xlsx"])

if uploaded:

    req_df = pd.read_excel(uploaded)
    req_df.columns = [c.strip() for c in req_df.columns]

    item_col = st.selectbox("عمود الصنف", req_df.columns)
    qty_col = st.selectbox("عمود الكمية", req_df.columns)

    if st.button("🔍 تنفيذ المطابقة الذكية"):

        rows = []

        for _, r in req_df.iterrows():
            item = str(r[item_col])
            qty = r[qty_col]

            match, score = smart_match(item)

            if match is not None:
                rows.append({
                    "Requested Item": item,
                    "Matched Item": match["item"],
                    "Match Score": score,
                    "Quantity": qty,
                    "Price": match["price"],
                    "Remarks": match["item"]
                })
            else:
                rows.append({
                    "Requested Item": item,
                    "Matched Item": "",
                    "Match Score": 0,
                    "Quantity": qty,
                    "Price": 0,
                    "Remarks": ""
                })

        result_df = pd.DataFrame(rows)

        st.session_state["quotation"] = result_df


# ----------------------------
# Results Table
# ----------------------------

if "quotation" in st.session_state:

    df = st.session_state["quotation"]

    st.subheader("📋 نتائج المطابقة")

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "Matched Item": st.column_config.SelectboxColumn(
                options=master_items
            )
        },
        use_container_width=True
    )

    # update price if changed
    for i, row in edited.iterrows():
        m = row["Matched Item"]
        price_row = master_df[master_df["item"] == m]

        if not price_row.empty:
            edited.loc[i, "Price"] = price_row["price"].values[0]

    st.session_state["quotation"] = edited

    # ----------------------------
    # Export
    # ----------------------------

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited.to_excel(writer, index=False)

    st.download_button(
        "⬇ تحميل ملف التسعير",
        data=buffer.getvalue(),
        file_name="quotation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
