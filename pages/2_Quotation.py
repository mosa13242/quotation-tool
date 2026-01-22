import streamlit as st
import pandas as pd

# ===============================
# Page config
# ===============================
st.set_page_config(
    page_title="Quotation",
    layout="wide"
)

# ===============================
# Title
# ===============================
st.title("Quotation")

st.info("💡 اكتب الملاحظات يدويًا في خانة REMARKS")

# ===============================
# Initialize data
# ===============================
if "quotation_df" not in st.session_state:
    st.session_state.quotation_df = pd.DataFrame(
        {
            "Item": [""],
            "REMARKS": [""],
            "Quantity": [1],
            "Unit Price": [0.0],
        }
    )

df = st.session_state.quotation_df

# ===============================
# Data editor
# ===============================
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Item": st.column_config.TextColumn(
            label="Item",
            disabled=True
        ),
        "REMARKS": st.column_config.TextColumn(
            label="REMARKS",
            help="اكتب الملاحظات أو الوصف يدويًا"
        ),
        "Quantity": st.column_config.NumberColumn(
            label="Quantity",
            min_value=0,
            step=1
        ),
        "Unit Price": st.column_config.NumberColumn(
            label="Unit Price",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        ),
    }
)

st.session_state.quotation_df = edited_df

# ===============================
# Calculation
# ===============================
if not edited_df.empty:
    edited_df["Total"] = edited_df["Quantity"] * edited_df["Unit Price"]

    st.subheader("Summary")
    st.dataframe(edited_df, use_container_width=True)

    st.success(
        f"Grand Total: {edited

