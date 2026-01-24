import streamlit as st
import pandas as pd
from thefuzz import process
import io

st.set_page_config(layout="wide")

st.title("📊 Quotation Tool")

# =====================================
# LOAD MASTER LIST
# =====================================

MASTER_FILE = "master_list.xlsx"

@st.cache_data
def load_master():
    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df

master_df = load_master()

# --------- detect columns ----------
cols_lower = {c.lower(): c for c in master_df.columns}

def find_col(name_list):
    for n in name_list:
        if n.lower() in cols_lower:
            return cols_lower[n.lower()]
    return None

ITEM_COL = find_col(["item", "product", "name", "description"])
PRICE_COL = find_col(["price", "unit price", "cost", "selling price", "rate"])

if not ITEM_COL or not PRICE_COL:
    st.error(
        f"❌ الماستر لازم يحتوي على عمود صنف وعمود سعر.\n"
        f"الأعمدة الموجودة: {list(master_df.columns)}"
    )
    st.stop()

master_items = master_df[ITEM_COL].astype(str).tolist()

# =====================================
# UPLOAD REQUEST FILE
# =====================================

uploaded = st.file_uploader("📤 ارفع ملف الطلب (Excel)", type=["xlsx"])

run_match = st.button("🔍 تنفيذ المطابقة الذكية")

# =====================================
# MATCH FUNCTION
# =====================================

def match_item(text):
    return process.extractOne(text, master_items)

# =====================================
# PROCESS
# =====================================

if uploaded and run_match:

    req_df = pd.read_excel(uploaded)
    req_df.columns = [c.strip() for c in req_df.columns]

    req_cols_lower = {c.lower(): c for c in req_df.columns}

    def find_req(name_list):
        for n in name_list:
            if n.lower() in req_cols_lower:
                return req_cols_lower[n.lower()]
        return None

    REQ_ITEM_COL = find_req(["item", "product", "description", "name"])
    QTY_COL = find_req(["qty", "quantity", "count", "amount"])

    if not REQ_ITEM_COL:
        st.error("❌ ملف الطلب لازم يحتوي عمود صنف")
        st.stop()

    results = []

    for _, row in req_df.iterrows():

        item_text = str(row[REQ_ITEM_COL])

        match, score = match_item(item_text)

        price_row = master_df[master_df[ITEM_COL] == match]

        price = (
            price_row[PRICE_COL].values[0]
            if not price_row.empty
            else 0
        )

        qty = row[QTY_COL] if QTY_COL and QTY_COL in row else 1

        results.append({
            "Requested Item": item_text,
            "Matched Item": match,
            "Match Score": score,
            "Quantity": qty,
            "Price": price,
            "Remarks": match,
            "Confirm": False
        })

    result_df = pd.DataFrame(results)

    st.success("✅ تمت المطابقة")

    # =====================================
    # EDITABLE TABLE
    # =====================================

    st.subheader("✏️ تعديل النتائج")

    edited_df = st.data_editor(
        result_df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Remarks": st.column_config.SelectboxColumn(
                "Remarks",
                options=master_items
            ),
            "Confirm": st.column_config.CheckboxColumn("Confirm"),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=1),
            "Price": st.column_config.NumberColumn("Price", min_value=0.0)
        }
    )

    # =====================================
    # DOWNLOAD RESULT
    # =====================================

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited_df.to_excel(writer, index=False)

    st.download_button(
        "⬇️ تحميل النتيجة Excel",
        buffer.getvalue(),
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
