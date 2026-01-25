import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz

st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# =========================
# Load Master List
# =========================
def load_master_safe():

    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["item", "price"])
        df.to_excel(MASTER_FILE, index=False)
        return df

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip().lower() for c in df.columns]

    df = df.dropna(subset=["item"])

    return df


master_df = load_master_safe()

# =========================
# Sidebar
# =========================
st.sidebar.title("📂 App")

page = st.sidebar.radio(
    "Pages",
    ["Master List", "Quotation"]
)

# =========================
# MASTER LIST PAGE
# =========================
if page == "Master List":

    st.title("📋 Master List")

    uploaded = st.file_uploader(
        "Upload Master Excel",
        type=["xlsx"]
    )

    if uploaded:
        df = pd.read_excel(uploaded)
        df.columns = [c.strip().lower() for c in df.columns]

        df.to_excel(MASTER_FILE, index=False)
        st.success("Master list saved successfully ✅")

        master_df = load_master_safe()

    st.subheader("Current Master Data")
    st.dataframe(master_df, use_container_width=True)

# =========================
# MATCHING FUNCTION
# =========================
def smart_match(query):

    q = str(query).lower()

    q_tokens = set(q.replace("/", " ").split())

    best_row = None
    best_score = 0

    for _, row in master_df.iterrows():

        m = str(row["item"]).lower()
        m_tokens = set(m.replace("/", " ").split())

        # 🔴 شرط كلمة كاملة مشتركة
        if len(q_tokens & m_tokens) == 0:
            continue

        score = fuzz.token_set_ratio(q, m)

        if score > best_score:
            best_score = score
            best_row = row

    if best_score < 45:
        return None, 0

    return best_row, best_score


# =========================
# QUOTATION PAGE
# =========================
if page == "Quotation":

    st.title("📑 Quotation Tool")

    uploaded_file = st.file_uploader(
        "Upload Quotation Excel",
        type=["xlsx"]
    )

    if uploaded_file:

        quote_df = pd.read_excel(uploaded_file)
        quote_df.columns = [c.strip() for c in quote_df.columns]

        st.subheader("Preview")
        st.dataframe(quote_df.head())

        item_col = st.selectbox(
            "عمود الصنف",
            quote_df.columns
        )

        qty_col = st.selectbox(
            "عمود الكمية",
            quote_df.columns
        )

        if st.button("🔍 تنفيذ المطابقة"):

            results = []

            for _, row in quote_df.iterrows():

                item = row[item_col]
                qty = row[qty_col]

                matched, score = smart_match(item)

                if matched is not None:

                    price = matched.get("price", 0)

                    results.append({
                        "Requested Item": item,
                        "Matched Item": matched["item"],
                        "Match Score": score,
                        "Quantity": qty,
                        "Price": price,
                        "Total": qty * price,
                        "Remarks": ""
                    })

                else:

                    results.append({
                        "Requested Item": item,
                        "Matched Item": None,
                        "Match Score": 0,
                        "Quantity": qty,
                        "Price": 0,
                        "Total": 0,
                        "Remarks": "No Match"
                    })

            result_df = pd.DataFrame(results)

            st.subheader("📊 Results")
            st.dataframe(result_df, use_container_width=True)

            # Download
            out_file = "quotation_result.xlsx"
            result_df.to_excel(out_file, index=False)

            with open(out_file, "rb") as f:
                st.download_button(
                    "⬇ Download Result Excel",
                    f,
                    file_name="quotation_result.xlsx"
                )
