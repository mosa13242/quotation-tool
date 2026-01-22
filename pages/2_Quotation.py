import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير المستقر", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ===============================
# Load / Init Master
# ===============================
def get_safe_master():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    names = df[df.columns[0]].astype(str).tolist()
    return df, names

master_df, master_names = get_safe_master()

st.title("🛡️ نظام التسعير (بحث + إضافة + حفظ)")

# ===============================
# Upload Client File
# ===============================
uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if not uploaded_file:
    st.stop()

df_client = pd.read_excel(uploaded_file)
df_client.columns = [str(c).strip() for c in df_client.columns]

# ===============================
# Column Mapping
# ===============================
col1, col2 = st.columns(2)
with col1:
    c_item = st.selectbox("عمود الصنف (طلبك):", df_client.columns)
    c_qty = st.selectbox("عمود الكمية (طلبك):", df_client.columns)

with col2:
    m_item = st.selectbox(
        "عمود الصنف (الماستر):",
        master_df.columns if not master_df.empty else ["Item"]
    )
    m_price = st.selectbox(
        "عمود السعر (الماستر):",
        master_df.columns if not master_df.empty else ["Price"]
    )

# ===============================
# Smart Match
# ===============================
if st.button("🔍 تنفيذ المطابقة الذكية"):
    def find_match(text):
        if not master_names:
            return str(text)
        match, score = process.extractOne(
            str(text), master_names, scorer=fuzz.token_set_ratio
        )
        return match if score >= 70 else str(text)

    df_client["REMARKS"] = df_client[c_item].apply(find_match)
    price_map = dict(zip(master_df[m_item], master_df[m_price]))
    df_client["Unit_Price"] = df_client["REMARKS"].map(price_map).fillna(0.0)

    st.session_state["df_current"] = df_client

# ===============================
# Edit & Approve
# ===============================
if "df_current" in st.session_state:
    st.info("✏️ عدّل REMARKS أو السعر يدويًا ثم اعتمد الحفظ")

    edited_df = st.data_editor(
        st.session_state["df_current"],
        use_container_width=True,
        num_rows="dynamic",
        disabled=[c_item, c_qty],
        column_config={
            "REMARKS": st.column_config.TextColumn("الصنف"),
            "Unit_Price": st.column_config.NumberColumn(
                "السعر", min_value=0.0, format="%.2f"
            ),
        },
        key="final_editor"
    )

    if st.button("🚀 اعتماد وحفظ الأصناف الجديدة"):
        new_rows = []
        f_master, f_names = get_safe_master()

        for _, row in edited_df.iterrows():
            name = str(row["REMARKS"]).strip()
            price = float(row["Unit_Price"])

            if name and name not in f_names:
                new_rows.append({m_item: name, m_price: price})
                f_names.append(name)

        if new_rows:
            updated_master = pd.concat(
                [f_master, pd.DataFrame(new_rows)],
                ignore_index=True
            )
            updated_master.to_excel(MASTER_FILE, index=False)
            st.success("✅ تم حفظ الأصناف الجديدة في الماستر")

        # ===============================
        # Final Calculation
        # ===============================
        edited_df[c_qty] = pd.to_numeric(
            edited_df[c_qty], errors="coerce"
        ).fillna(0)

        edited_df["Total"] = edited_df[c_qty] * edited_df["Unit_Price"]

        st.subheader("📊 النتيجة النهائية")
        st.dataframe(edited_df, use_container_width=True)

        total_val = edited_df["Total"].sum()
        st.metric("💰 الإجمالي الكلي", f"{total_val:,.2f}")

