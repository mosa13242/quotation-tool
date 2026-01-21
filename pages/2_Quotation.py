import streamlit as st
import pandas as pd
import sqlite3

st.title("📄 Quotation")

# اتصال بقاعدة البيانات
conn = sqlite3.connect("quotation.db")
df = pd.read_sql("SELECT * FROM master_items", conn)
conn.close()

# لو الماستر ليست فاضية
if df.empty:
    st.warning("⚠️ Master List is empty. Please upload data first.")
    st.stop()

# اختيار الصنف
item = st.selectbox(
    "Select Item",
    df["ITEM"].unique()
)

# جلب بيانات الصنف المختار
selected_item = df[df["ITEM"] == item].iloc[0]

unit_price = selected_item["Unit price L"]
vat_percent = selected_item["VAT %"]

st.write(f"**Unit Price:** {unit_price}")
st.write(f"**VAT %:** {vat_percent}")

# إدخال الكمية
qty = st.number_input("Quantity", min_value=1, value=1)

# الحسابات
price_before_vat = unit_price * qty
vat_value = price_before_vat * (vat_percent / 100)
total_price = price_before_vat + vat_value

st.divider()
st.write(f"**Price Before VAT:** {price_before_vat}")
st.write(f"**VAT Value:** {vat_value}")
st.write(f"### 💰 Total Price: {total_price}")
