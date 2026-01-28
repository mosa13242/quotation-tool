import streamlit as st
import pandas as pd
import os
import difflib

MASTER_FILE = "master_list.xlsx"

st.set_page_config(page_title="Quotation", layout="wide")

st.title("🧾 Quotation Generator")

# -----------------------------
# Load Master List
# -----------------------------

def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["item", "price"])
        df.to_excel(MASTER_FILE, index=False)
        return df

    df = pd.read_excel(MASTER_FILE)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df


master_df = load_master()

if master_df.empty:
    st.error("❌ Master List فارغة — أضف أصناف وأسعار أولاً.")
    st.stop()

master_items = master_df["item"].astype(str).tolist()

# -----------------------------
# Upload RFQ
# -----------------------------

rfq_file = st.file_uploader("📤 Upload RFQ Excel", type=["xlsx"])

if rfq_file:

    rfq_df = pd.read_excel(rfq_file)

    rfq_df.columns = (
        rfq_df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    st.subheader("RFQ Preview")
    st.dataframe(rfq_df)

    item_col = st.selectbox("📦 اختر عمود الصنف", rfq_df.columns)
    qty_col = st.selectbox("📊 اختر عمود الكمية", rfq_df.columns)

    if st.button("🚀 Generate Pricing"):

        rows = []

        for _, row in rfq_df.iterrows():

            rfq_item = str(row[item_col])

            matches = difflib.get_close_matches(
                rfq_item,
                master_items,
                n=1,
                cutoff=0.4
            )

            matched_item = matches[0] if matches else ""
            price = None

            if matched_item:
                price = master_df.loc[
                    master_df["item"] == matched_item,
                    "price"
                ].values[0]

            rows.append({
                "rfq_item": rfq_item,
                "matched_item": matched_item,
                "quantity": row[qty_col],
                "price": price,
            })

        result_df = pd.DataFrame(rows)

        # Calculate total
        result_df["total"] = (
            pd.to_numeric(result_df["quantity"], errors="coerce")
            * pd.to_numeric(result_df["price"], errors="coerce")
        )

        st.subheader("✍ Editable Pricing Table")

        edited_df = st.data_editor(
            result_df,
            num_rows="dynamic",
            use_container_width=True
        )

        # Recalculate after edits
        edited_df["total"] = (
            pd.to_numeric(edited_df["quantity"], errors="coerce")
            * pd.to_numeric(edited_df["price"], errors="coerce")
        )

        st.success("✅ Pricing ready")

        st.dataframe(edited_df)

        # Download Excel
        st.download_button(
            "⬇ Download Quotation Excel",
            edited_df.to_excel(index=False),
            file_name="quotation.xlsx"
        )
