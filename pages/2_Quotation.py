import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(
    page_title="Quotation",
    layout="wide"
)

st.title("Quotation")

# بيانات تجريبية
df = pd.DataFrame({
    "Item": [
        "Item A",
        "Item B",
        "Item C"
    ],
    "REMARKS": [
        "",
        "",
        ""
    ]
})

# بيانات الاقتراحات
master_names = [
    "Option 1",
    "Option 2",
    "Option 3"
]

# رسالة توضيحية (مهمة – بدون كسر string)
st.info("""
💡 للاختيار اكتب اسمًا موجودًا
أو ابدأ بالكتابة في REMARKS
""")

# جدول الإدخال
edited_df = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Item": st.column_config.TextColumn(
            label="Item",
            disabled=True
        ),
        "REMARKS": st.column_config.TextColumn(
            label="REMARKS",
            help="اكتب ملاحظة أو اختر من الاقتراحات",
            suggestions=master_names,
            width="large"
        ),
    }
)

# عرض النتيجة
st.subheader("Preview")
st.dataframe(
    edited_df,
    use_container_width=True
)
