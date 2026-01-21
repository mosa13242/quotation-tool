import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quotation Tool", layout="wide")

st.title("🧾 Quotation Tool")
st.write("Upload Excel file and generate quotation")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Data Preview")
    st.dataframe(df)

    if "Price" in df.columns:
        total = df["Price"].sum()
        st.subheader("Total Price")
        st.success(f"{total:,.2f}")
