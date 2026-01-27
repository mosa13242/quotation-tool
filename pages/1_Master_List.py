import streamlit as st
import pandas as pd
import os

MASTER_FILE = "master_list.xlsx"

st.set_page_config(page_title="Master List", layout="wide")

st.title("📦 Master List Manager")

# -------------------------
# Load or create master
# -------------------------

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

# -------------------------
# Display + edit
# -------------------------

st.subheader("📋 Current Items")

edited_df = st.data_editor(
    master_df,
    num_rows="dynamic",
    use_container_width=True
)

# -------------------------
# Save changes
# -------------------------

if st.button("💾 Save Master List"):
    edited_df.to_excel(MASTER_FILE, index=False)
    st.success("Master list saved successfully ✅")

# -------------------------
# Upload replace
# -------------------------

st.divider()
st.subheader("📤 Upload new master list")

uploaded = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded:
    new_df = pd.read_excel(uploaded)

    new_df.columns = (
        new_df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    if not {"item", "price"}.issubset(new_df.columns):
        st.error("❌ Excel must contain columns: item, price")
    else:
        new_df.to_excel(MASTER_FILE, index=False)
        st.success("Master list replaced ✅")
        st.rerun()

# -------------------------
# Download backup
# -------------------------

st.divider()

with open(MASTER_FILE, "rb") as f:
    st.download_button(
        "⬇ Download Master Backup",
        f,
        file_name="master_list.xlsx"
    )
