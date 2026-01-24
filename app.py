import streamlit as st
import pandas as pd
import os
import pdfplumber
from thefuzz import process, fuzz

st.set_page_config(page_title="Quotation System", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ---------------------------
# تحميل الماستر
# ---------------------------
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)

    df = pd.read_excel(MASTER_FILE)
    df.columns = df.columns.str.strip()
    return df


master_df = load_master()
master_items = master_df["Item"].astype(str).tolist() if not master_df.empty else []


# ---------------------------
# PDF Reader
# ---------------------------
def read_pdf(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                rows.extend(table[1:])

    return pd.DataFrame(rows)


# ---------------------------
# Fuzzy Match
# ---------------------------
def match_item(text):
    if not master_items:
        return text, 0

    match, score = process.extractOne(
        str(text),
        master_items,
        scorer=fuzz.token_set_ratio,
    )

    if score >= 70:
        return match, score
    return text, score


# ---------------------------
# UI
# ---------------------------

st.title("📊 Smart Quotation System")

tab1, tab2 = st.tabs(["📋 Master List", "💰 Quotation"])

# =======================
# MASTER LIST
# =======================
with tab1:

    st.subheader("📦 Master List")

    master_editor = st.data_editor(
        master_df,
        num_rows="dynamic",
        use_container_width=True,
    )

    if st.button("💾 Save Master List"):
        master_editor.to_excel(MASTER_FILE, index=False)
        st.success("Master List Saved ✔")
        st.rerun()


# =======================
# QUOTATION
# =======================
with tab2:

    st.subheader("📤 Upload Excel or PDF")

    uploaded = st.file_uploader(
        "Upload client file",
        type=["xlsx", "xls", "pdf"]
    )

    if uploaded:

        # ----------- READ FILE
        if uploaded.name.endswith(".pdf"):
            df_client = read_pdf(uploaded)
            st.warning("PDF extracted – check columns carefully.")
        else:
            df_client = pd.read_excel(uploaded)

        df_client.columns = df_client.columns.astype(str)

        st.write("### 🔧 Column Mapping")

        col1, col2, col3 = st.columns(3)

        with col1:
            client_item_col = st.selectbox("Item Column", df_client.columns)

        with col2:
            qty_col = st.selectbox("Quantity Column", df_client.columns)

        with col3:
            price_col = st.selectbox(
                "Price Column (optional)",
                ["None"] + list(df_client.columns)
            )

        # ----------- MATCH
        if st.button("🔍 Run Pricing"):

            remarks = []
            prices = []

            price_map = dict(
                zip(
                    master_df["Item"].astype(str),
                    master_df["Price"]
                )
            )

            for val in df_client[client_item_col]:

                matched, score = match_item(val)
                remarks.append(matched)

                prices.append(price_map.get(matched, 0))

            df_client["REMARKS"] = remarks
            df_client["Unit_Price"] = prices

            st.session_state["quote"] = df_client

        # ----------- EDITOR
        if "quote" in st.session_state:

            st.info("✍️ You can edit item or price manually")

            edited = st.data_editor(
                st.session_state["quote"],
                column_config={
                    "REMARKS": st.column_config.TextColumn(
                        "Matched Item",
                        suggestions=master_items,
                    ),
                    "Unit_Price": st.column_config.NumberColumn(
                        "Unit Price",
                        min_value=0.0
                    )
                },
                use_container_width=True,
                num_rows="fixed"
            )

            # -------- SAVE NEW ITEMS
            if st.button("💾 Save new items to Master & Calculate"):

                new_rows = []

                for _, row in edited.iterrows():
                    item = str(row["REMARKS"]).strip()
                    price = float(row["Unit_Price"])

                    if (
                        item
                        and item not in master_items
                        and price > 0
                    ):
                        new_rows.append({
                            "Item": item,
                            "Price": price
                        })

                if new_rows:
                    updated_master = pd.concat(
                        [master_df, pd.DataFrame(new_rows)],
                        ignore_index=True
                    )
                    updated_master.to_excel(MASTER_FILE, index=False)
                    st.success(f"Added {len(new_rows)} new items to master ✔")
                    st.rerun()

                # -------- TOTAL
                edited[qty_col] = pd.to_numeric(
                    edited[qty_col], errors="coerce"
                ).fillna(0)

                edited["Total"] = edited[qty_col] * edited["Unit_Price"]

                st.write("### ✅ Final Quotation")
                st.dataframe(edited, use_container_width=True)

                st.metric(
                    "Grand Total",
                    f"{edited['Total'].sum():,.2f}"
                )
