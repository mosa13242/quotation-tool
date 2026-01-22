import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

# ================== إعداد الصفحة ==================
st.set_page_config(
    page_title="Quotation System",
    layout="wide"
)

MASTER_FILE = "master_list.xlsx"

# ================== تحميل الماستر ==================
def load_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []

    df = pd.read_excel(MASTER_FILE)
    df.columns = [c.strip() for c in df.columns]
    names = df["Item"].astype(str).unique().tolist()
    return df, names


master_df, master_names = load_master()

st.title("📄 نظام التسعير والبحث الذكي")

# ================== رفع ملف العميل ==================
uploaded_file = st.file_uploader(
    "📤 ارفع ملف طلب العميل (Excel)",
    type=["xlsx"]
)

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [c.strip() for c in df_client.columns]

    st.subheader("⚙️ ربط الأعمدة")

    col1, col2 = st.columns(2)

    with col1:
        c_item = st.selectbox("عمود الصنف (عندك)", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك)", df_client.columns)

    with col2:
        m_item = st.selectbox("عمود الصنف (الماستر)", master_df.columns)
        m_price = st.selectbox("عمود السعر (الماستر)", master_df.columns)

    # ================== البحث الذكي ==================
    if st.button("🔍 تنفيذ البحث والتسعير"):
        def smart_match(text):
            if not master_names:
                return str(text)

            match, score = process.extractOne(
                str(text),
                master_names,
                scorer=fuzz.token_set_ratio
            )

            return match if score >= 70 else str(text)

        df_client["REMARKS"] = df_client[c_item].apply(smart_match)

        price_map = dict(zip(master_df[m_item], master_df[m_price]))
        df_client["Unit_Price"] = df_client["REMARKS"].map(price_map).fillna(0.0)

        st.session_state["quote_df"] = df_client.copy()

    # ================== جدول التعديل ==================
    if "quote_df" in st.session_state:
        st.info("✍️ اكتب أو اختَر الصنف في خانة REMARKS")

        edited_df = st.data_editor(
            st.session_state["quote_df"],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو جديد)",
                    suggestions=master_names,
                    help="اختَر من الماستر أو اكتب صنف جديد"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "سعر الوحدة",
                    format="%.2f",
                    min_value=0.0
                )
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="editor"
        )

        # ================== حفظ + حساب ==================
        if st.button("💾 اعتماد الفاتورة وحفظ الجديد"):
            latest_master, latest_names = load_master()
            new_rows = []

            for _, row in edited_df.iterrows():
                name = str(row["REMARKS"]).strip()
                price = float(row["Unit_Price"])

                if name and name not in latest_names:
                    new_rows.append({
                        m_item: name,
                        m_price: price
                    })
                    latest_names.append(name)

            if new_rows:
                updated_master = pd.concat(
                    [latest_master, pd.DataFrame(new_rows)],
                    ignore_index=True
                )
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم إضافة {len(new_rows)} صنف جديد للماستر")

            edited_df[c_qty] = pd.to_numeric(
                edited_df[c_qty],
                errors="coerce"
            ).fillna(0)

            edited_df["Total"] = edited_df[c_qty] * edited_df["Unit_Price"]

            st.subheader("📊 الفاتورة النهائية")
            st.dataframe(edited_df, use_container_width=True)

            st.metric(
                "💰 الإجمالي",
                f"{edited_df['Total'].sum():,.2f}"
            )

