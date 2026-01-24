import streamlit as st
import pandas as pd
import os
from thefuzz import process

st.set_page_config(page_title="Quotation System", layout="wide")

MASTER_FILE = "master_list.xlsx"
CLIENT_FILE = "clients_prices.xlsx"

# -------------------------------
# Create files if not exist
# -------------------------------

if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=["Item", "Price"]).to_excel(MASTER_FILE, index=False)

if not os.path.exists(CLIENT_FILE):
    pd.DataFrame(columns=["Client", "Item", "Price"]).to_excel(CLIENT_FILE, index=False)

master_df = pd.read_excel(MASTER_FILE)
clients_df = pd.read_excel(CLIENT_FILE)

master_items = master_df["Item"].astype(str).tolist()

# -------------------------------
# UI
# -------------------------------

st.title("💰 نظام التسعير والبحث الذكي")

# -------------------------------
# CLIENT SECTION
# -------------------------------

st.subheader("👤 اختيار العميل")

clients_list = sorted(clients_df["Client"].dropna().unique().tolist())

col1, col2 = st.columns(2)

with col1:
    client_name = st.selectbox("اختر عميل موجود", [""] + clients_list)

with col2:
    new_client = st.text_input("➕ إضافة عميل جديد")

if st.button("💾 حفظ العميل"):
    if new_client:
        new_row = pd.DataFrame([[new_client, "", ""]], columns=["Client", "Item", "Price"])
        clients_df = pd.concat([clients_df, new_row], ignore_index=True)
        clients_df.to_excel(CLIENT_FILE, index=False)
        st.success("تم إضافة العميل")

# -------------------------------
# Upload file
# -------------------------------

st.divider()
st.subheader("📂 رفع ملف طلب العميل")

uploaded_file = st.file_uploader("ارفع ملف الطلب", type=["xlsx"])

if uploaded_file:

    request_df = pd.read_excel(uploaded_file)

    st.write("📄 البيانات:")
    st.dataframe(request_df)

    item_col = st.selectbox("عمود الأصناف", request_df.columns)
    qty_col = st.selectbox("عمود الكمية", request_df.columns)

    if st.button("🔍 تنفيذ المطابقة"):

        results = []

        for _, row in request_df.iterrows():

            item = str(row[item_col])

            match, score = process.extractOne(item, master_items)

            price = master_df.loc[master_df["Item"] == match, "Price"].values[0]

            # Client price?
            client_price = price

            if client_name:
                mask = (
                    (clients_df["Client"] == client_name) &
                    (clients_df["Item"] == match)
                )
                if mask.any():
                    client_price = clients_df.loc[mask, "Price"].values[0]

            results.append({
                "Requested_Item": item,
                "Matched_Item": match,
                "Quantity": row[qty_col],
                "Client_Price": client_price,
                "Confirmed": False,
                "Notes": ""
            })

        result_df = pd.DataFrame(results)

        st.subheader("📊 النتائج")

        edited_df = st.data_editor(
            result_df,
            use_container_width=True,
            column_config={
                "Confirmed": st.column_config.CheckboxColumn("✔ Confirm")
            }
        )

        # -------------------------------
        # SAVE CONFIRMED PRICES
        # -------------------------------

        if st.button("💾 حفظ الأسعار المؤكدة"):

            if not client_name:
                st.warning("اختر عميل أولاً")
            else:

                confirmed_rows = edited_df[edited_df["Confirmed"] == True]

                for _, row in confirmed_rows.iterrows():

                    mask = (
                        (clients_df["Client"] == client_name) &
                        (clients_df["Item"] == row["Matched_Item"])
                    )

                    if mask.any():
                        clients_df.loc[mask, "Price"] = row["Client_Price"]
                    else:
                        new_row = pd.DataFrame(
                            [[client_name, row["Matched_Item"], row["Client_Price"]]],
                            columns=["Client", "Item", "Price"]
                        )
                        clients_df = pd.concat([clients_df, new_row], ignore_index=True)

                clients_df.to_excel(CLIENT_FILE, index=False)

                st.success("✅ تم حفظ أسعار العميل بنجاح")
