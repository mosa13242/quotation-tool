import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

st.title("📊 Quotation Tool")
st.subheader("Quotation Matching System")

# =============================
# Load Master List
# =============================

@st.cache_data
def load_master():
    if not os.path.exists(MASTER_FILE):
        return pd.DataFrame(columns=["Item", "unit_price"])

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


master_df = load_master()

# =============================
# Upload RFQ File
# =============================

uploaded_file = st.file_uploader(
    "📄 ارفع ملف الطلب",
    type=["xlsx"]
)

if uploaded_file:

    rfq_df = pd.read_excel(uploaded_file)
    rfq_df.columns = [c.strip().lower() for c in rfq_df.columns]

    st.success("✅ تم رفع الملف")

    st.dataframe(rfq_df)

    # =============================
    # Choose Column
    # =============================

    col1, col2 = st.columns(2)

    with col1:
        item_col = st.selectbox(
            "📝 اختر عمود اسم الصنف",
            rfq_df.columns
        )

    with col2:
        qty_col = st.selectbox(
            "📦 اختر عمود الكمية",
            rfq_df.columns
        )

    # =============================
    # Run Pricing
    # =============================

    if st.button("🚀 تشغيل التسعير"):

        results = []

        master_items = master_df["item"].astype(str).str.upper().str.strip()
        price_map = dict(
            zip(master_items, master_df["unit_price"])
        )

        for _, row in rfq_df.iterrows():

            name = str(row[item_col]).upper().strip()
            qty = row[qty_col]

            if name in price_map:
                price = price_map[name]
                score = 100
                remark = name
            else:
                price = ""
                score = 0
                remark = "NO MATCH"

            results.append({
                "Requested Item": name,
                "Matched Item": remark,
                "Match Score": score,
                "Quantity": qty,
                "Price": price,
                "Total": price * qty if price != "" else "",
                "Remarks": remark
            })

        edited = pd.DataFrame(results)

        st.divider()
        st.subheader("📋 Results")

        st.dataframe(edited, use_container_width=True)

        # =============================
        # Download Excel
        # =============================

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            edited.to_excel(writer, index=False)

        st.download_button(
            label="📥 تحميل ملف التسعير",
            data=output.getvalue(),
            file_name="quotation_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


