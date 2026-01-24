import streamlit as st
import pandas as pd
from thefuzz import process
import io

st.set_page_config(layout="wide")

st.title("📊 Quotation Tool")

# ================================
# LOAD MASTER LIST
# ================================

MASTER_FILE = "master_list.xlsx"

@st.cache_data
def load_master():
    return pd.read_excel(MASTER_FILE)

master_df = load_master()
master_items = master_df["Item"].astype(str).tolist()

# ================================
# UPLOAD REQUEST FILE
# ================================

uploaded = st.file_uploader("📤 ارفع ملف الطلب (Excel)", type=["xlsx"])

run_match = st.button("🔍 تنفيذ المطابقة الذكية")

# ================================
# MATCHING FUNCTION
# ================================

def match_item(text):
    result = process.extractOne(text, master_items)
    return result

# ================================
# PROCESS
# ================================

if uploaded and run_match:

    req_df = pd.read_excel(uploaded)

    if "Item" not in req_df.columns:
        st.error("❌ ملف الطلب لازم يحتوي على عمود اسمه Item")
        st.stop()

    results = []

    for item in req_df["Item"]:

        match, score = match_item(str(item))

        price_row = master_df[master_df["Item"] == match]

        price = (
            price_row["Price"].values[0]
            if not price_row.empty
            else 0
        )

        results.append({
            "Requested Item": item,
            "Matched Item": match,
            "Match Score": score,
            "Quantity": 1,
            "Price": price,
            "Remarks": match,
            "Confirm": False
        })

    result_df = pd.DataFrame(results)

    st.success("✅ تمت المطابقة")

    # ================================
    # EDITABLE TABLE
    # ================================

    st.subheader("✏️ تعديل النتائج")

    edited_df = st.data_editor(
        result_df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Remarks": st.column_config.SelectboxColumn(
                "Remarks",
                options=master_items,
                required=False
            ),
            "Confirm": st.column_config.CheckboxColumn("Confirm"),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=1),
            "Price": st.column_config.NumberColumn("Price")
        }
    )

    # ================================
    # DOWNLOAD RESULT
    # ================================

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited_df.to_excel(writer, index=False)

    st.download_button(
        "⬇️ تحميل النتيجة Excel",
        buffer.getvalue(),
        file_name="quotation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
