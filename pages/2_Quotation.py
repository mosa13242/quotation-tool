import streamlit as st
import pandas as pd
from thefuzz import process
import io

st.set_page_config(layout="wide")

st.title("💰 نظام التسعير والبحث الذكي")

# ============================
# LOAD MASTER LIST
# ============================

MASTER_FILE = "master_list.xlsx"

@st.cache_data
def load_master():
    return pd.read_excel(MASTER_FILE)

master_df = load_master()

master_item_col = master_df.columns[0]
master_price_col = master_df.columns[1]

# ============================
# UPLOAD FILE
# ============================

uploaded = st.file_uploader(
    "📤 ارفع ملف طلب العميل",
    type=["xlsx"]
)

if not uploaded:
    st.stop()

rfq_df = pd.read_excel(uploaded)

st.subheader("📄 معاينة الملف")
st.dataframe(rfq_df.head())

# ============================
# COLUMN MAPPING
# ============================

st.subheader("⚙️ ربط الأعمدة")

col1, col2 = st.columns(2)

with col1:
    rfq_item_col = st.selectbox(
        "عمود الصنف (طلب العميل)",
        rfq_df.columns
    )

with col2:
    rfq_qty_col = st.selectbox(
        "عمود الكمية",
        rfq_df.columns
    )

if st.button("🔍 تنفيذ المطابقة الذكية"):

    result_rows = []

    for _, row in rfq_df.iterrows():

        query = str(row[rfq_item_col])

        match, score = process.extractOne(
            query,
            master_df[master_item_col].astype(str)
        )

        price_row = master_df.loc[
            master_df[master_item_col] == match,
            master_price_col
        ]

        price = price_row.values[0] if not price_row.empty else 0

        result_rows.append({
            "Requested Item": query,
            "Matched Item": match,
            "Score": score,
            "Quantity": row[rfq_qty_col],
            "Price": float(price),
            "Remarks": "",
            "Confirmed": False
        })

    st.session_state["quotation_df"] = pd.DataFrame(result_rows)

# ============================
# SHOW RESULT
# ============================

if "quotation_df" in st.session_state:

    st.subheader("📊 نتائج المطابقة")

    master_items = master_df[master_item_col].astype(str).tolist()

    edited_df = st.data_editor(
        st.session_state["quotation_df"],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Matched Item": st.column_config.SelectboxColumn(
                "Matched Item",
                options=master_items,
                required=True
            ),
            "Confirmed": st.column_config.CheckboxColumn(
                "Confirm"
            ),
            "Remarks": st.column_config.TextColumn(
                "Remarks"
            )
        }
    )

    # ============================
    # UPDATE PRICE WHEN ITEM CHANGES
    # ============================

    for idx, row in edited_df.iterrows():

        item = row["Matched Item"]

        price_row = master_df.loc[
            master_df[master_item_col] == item,
            master_price_col
        ]

        if not price_row.empty:
            edited_df.at[idx, "Price"] = float(price_row.values[0])

    st.session_state["quotation_df"] = edited_df

    # ============================
    # DOWNLOAD RESULT
    # ============================

    buffer = io.BytesIO()

with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    edited_df.to_excel(writer, index=False)

buffer.seek(0)
    st.download_button(
        "⬇ تحميل نتيجة التسعير",
        data=buffer.getvalue(),
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
