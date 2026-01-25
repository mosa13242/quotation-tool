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
# Load Master
# ---------------------------------------------------

@st.cache_data
def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["item", "price"])

    df = pd.read_excel(MASTER_FILE)
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
        
    return df

master_df = load_master()
master_items = master_df["item"].astype(str).tolist()

# ---------------------------------------------------
# Cleaning
# ---------------------------------------------------

IGNORE_WORDS = {
    "mg", "ml", "tab", "tablet", "tablets", "cap", "capsule",
    "syrup", "cream", "solution", "inj", "amp", "pcs", "packet"
}

def normalize(text):
    tokens = []
    for t in clean_text(text).split():
        if t not in IGNORE_WORDS and not t.isdigit():
            tokens.append(t)
    return " ".join(tokens)

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ---------------------------------------------------
# Word based matching
# ---------------------------------------------------

def token_match_score(a, b):
    a_tokens = set(clean_text(a).split())
    b_tokens = set(clean_text(b).split())
    
    if not a_tokens or not b_tokens:
        return 0

    common = a_tokens.intersection(b_tokens)
    return int((len(common) / len(a_tokens)) * 100)

def smart_match(query):
    q_norm = normalize(query)
    best_row = None
    best_score = 0

    for _, row in master_df.iterrows():
        m_norm = row["norm"]  # Ensure "norm" column exists
        q_words = set(q_norm.split())
        m_words = set(m_norm.split())

        if not q_words:
            continue

        overlap = len(q_words & m_words) / len(q_words)
        fuzzy = fuzz.token_set_ratio(q_norm, m_norm) / 100
        score = overlap * 0.75 + fuzzy * 0.25

        if score > best_score:
            best_score = score
            best_row = row

    # Set a minimum strict limit
    if best_score < 40:
        return None, best_score

    return best_row, round(best_score * 100)

# ---------------------------------------------------
# UI
# ---------------------------------------------------

st.title("📊 Quotation Tool")
st.title("Quotation Matching System")

uploaded = st.file_uploader("📄 ارفع ملف الطلب", type=["xlsx"])

if uploaded:
    if not master_df.empty:
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

    if "quotation" in st.session_state:
        df = st.session_state["quotation"]
        st.subheader("📋 Results")
        
        edited = st.data_editor(
            df,
            column_config={
                "Matched Item": st.column_config.SelectboxColumn(
                    options=master_items
                )
            },
            use_container_width=True
        )

        results = []
        
        for _, row in edited.iterrows():
            requested = row["Requested Item"]
            qty = row["Quantity"]
            matched = row["Matched Item"]
            price = master_df.loc[
                master_df["item"] == matched,
                "price"
            ].values[0] if matched in master_df["item"].values else 0
            
            results.append({
                "Requested Item": requested,
                "Matched Item": matched,
                "Match Score": row["Match Score"],
                "Quantity": qty,
                "Price": price,
                "Remarks": matched
            })

        result_df = pd.DataFrame(results)

        st.download_button(
            "Download Quotation",
            result_df.to_excel(index=False),
            file_name="quotation.xlsx"
        )



