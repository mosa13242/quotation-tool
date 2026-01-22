import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quotation", layout="wide")

st.title("Quotation")

st.info("💡 للاختيار اكتب النص يدويًا في خانة REMARKS")

# ===============================
# Data
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
# Dat

