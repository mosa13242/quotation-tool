import streamlit as st
import pandas as pd
import io
from thefuzz import process

st.set_page_config(page_title="Quotation Tool", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ============================
# LOAD MASTER
# ============================

@st.cache_data
def load_master():
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df

master_df = load_master()

# ============================
# AUTO COLUMN DETECT
# ============================

def find_col(possible):
    for name in possible:
        for col in master_df.columns:
            if name.lower() == col.lower():
                return col
    return None

ITEM_COL = find_col(["item", "product", "description", "name"])
PRICE_COL = find_col(["price", "unit_price", "unit price", "cost", "selling"])

if not ITEM_COL:
    st.error("❌ الماستر لازم يحتوي على عمود Item")
    st.stop()

if not PRICE_COL:
    st.error(f"❌ لا يوجد عمود سعر. الأعمدة: {list(master_df.columns)}")
    st.stop()

master_items = master_df[ITEM_COL].astype(str).tolist()

# ============================
# UI
# ============================

st.title("📊 Quotation Tool")

uploaded_file = st.file_uploader(
    "📤 ارفع ملف الطلب (Excel)",
    type=["xlsx"]
)

if not uploaded_file:
    st.stop()

rfq_df = pd.read_excel(uploaded_file)
rfq_df.columns = [c.strip() for c in rfq_df.columns]

st.subheader("⚙️ اختار الأعمدة")

item_col = st.selectbox("عمود الصنف", rfq_df.columns)
qty_col = st.selectbox("عمود الكمية", rfq_df.columns)

# ============================
# MATCH BUTTON
# ============================

if st.button("🔍 تنفيذ المطابقة الذكية"):

    results = []

    for _, row in rfq_df.iterrows():

        query = str(row[item_col])

        match, score = process.extractOne(query, master_items)

        price_row = master_df[master_df[ITEM_COL] == match]

        price = (
            price_row[PRICE_COL].values[0]
            if not price_row.empty
            else 0
        )

        results.append({
            "Requested Item": query,
            "Matched Item": match,
            "Match Score": score,
            "Quantity": row[qty_col],
            "Price": price,
            "Remarks": match,
            "Confirm": False
        })

    result_df = pd.DataFrame(results)

    st.session_state["quotation"] = result_df

# ============================
# EDITABLE TABLE
# ============================

if "quotation" in st.session_state:

    st.subheader("📋 نتائج المطابقة")

    df = st.session_state["quotation"]

    edited_df = st.data_editor(
        df,
        column_config={
            "Remarks": st.column_config.SelectboxColumn(
                "Remarks",
                options=master_items,
                required=True
            ),
            "Confirm": st.column_config.CheckboxColumn(
                "Confirm"
            )
        },
        use_container_width=True,
        num_rows="fixed"
    )

    st.session_state["quotation"] = edited_df

    # ============================
    # DOWNLOAD
    # ============================

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited_df.to_excel(writer, index=False)

    st.download_button(
        "⬇ تحميل ملف التسعير",
        buffer.getvalue(),
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
