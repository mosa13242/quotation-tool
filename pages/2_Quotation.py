import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quotation", layout="wide")

st.title("Quotation")

# رسالة إرشادية
st.info("💡 للاختيار اكتب اسمًا موجودًا أو ابدأ بالكتابة في REMARKS")

# ===============================
# بيانات تجريبية (غيّرها براحتك)
# ===============================
master_names = [
    "Item A",
    "Item B",
    "Item C",
    "Service X",
    "Service Y"
]

# إنشاء DataFrame مبدئي
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
# جدول الإدخال
# ===============================
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Item": st.column_config.TextColumn(
            label="Item",
            disabled=True
        ),
        "REMARKS": st.column_config.TextColumn(
            label="REMARKS",
            help="اختر من الاقتراحات أو اكتب يدويًا",
            suggestions=master_names
        ),
        "Quantity": st.column_config.NumberColumn(
            label="Quantity",
            min_value=0,
            step=1
        ),
        "Unit Price": st.column_config.NumberColumn(
            label="Unit Price",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        ),
    }
)

# حفظ التعديلات
st.session_state.quotation_df = edited_df

# ===============================
# حساب الإجمالي
# ===============================
if not edited_df.empty:
    edited_df["Total"] = edited_df["Quantity"] * edited_df["Unit Price"]

    st.subheader("Summary")
    st.dataframe(
        edited_df,
        use_container_width=True
    )

    grand_total = edited_df["Total"].sum()
    st.success(f"Grand Total: {grand_total:,.2f}")

