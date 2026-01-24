import streamlit as st
import os

# ===== AUTH =====
from auth import require_login, logout_button

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Quotation Tool",
    layout="wide",
)

# ===== LOGIN REQUIRED =====
require_login()

# ===== SIDEBAR =====
with st.sidebar:
    st.title("📊 Quotation Tool")
    logout_button()

    st.markdown("---")

    page = st.radio(
        "📂 القائمة",
        ["Master List", "Quotation"]
    )

# ===== ROUTER =====
if page == "Master List":
    st.switch_page("pages/1_Master_List.py")

elif page == "Quotation":
    st.switch_page("pages/2_Quotation.py")
