import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quotation", layout="wide")

st.title("Quotation")

# بيانات تجريبية
data = {
    "Item": ["Item A", "Item B", "Item C"],
    "REMARKS": ["", "", ""],
}

df = pd.DataFrame(data)

master_names = ["Option 1", "Option 2", "Option 3"]

st.info("""
💡 للاختيار، اكتب اسمًا موجودًا أو ابدأ بالكتابة في REMARKS
""")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    column_config={
        "Item": st.column_config.TextColumn(
            "Item",
            disabled=True
        ),
        "REMARKS": st.column_config.TextColumn(
            label="REMARKS",
            help="اكتب ملاحظة أو اختر من الاقتراحات",
            suggestions=master_names,
            width="large"
        ),
    },
    hide_index=True
)

st.subheader("النتيجة")
st.dataframe(edited_df, use_container_width=True)

