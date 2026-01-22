import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير المستقر", layout="wide")

MASTER_FILE = "master_list.xlsx"

# ===============================
# Load / Create Master List Safely
# ===============================
def load_master_safe():
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=["Item", "Price"])
        df.to_excel(MASTER_FILE, index=False)
        return df, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master_safe()

st.title("🛡️ نظام التسعير (بحث + إضافة + حفظ)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]

    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (طلب العميل):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (طلب العميل):", df_client.columns)
    with c2:
        m_item = st.selectbox(
            "عمود الصنف (الماستر):",
            master_df.columns if not master_df.empty else ["Item"]
        )
        m_price = st.selectbox(
            "عمود السعر (الماستر):",
            master_df.columns if not master_df.empty else ["Price"]
        )

    if st.button("🔍 تنفيذ المطابقة"):
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

        price_map = dict(zip(
            master_df[m_item].astype(str),
            master_df[m_price]
        ))

        df_client["Unit_Price"] = (
            df_client["REMARKS"]
            .map(price_map)
            .fillna(0.0)
        )

        st.session_state["df_working"] = df_client

    if "df_working" in st.session_state:
        st.success(
            "✏️ عدّل REMARKS أو أضف صنف جديد + سعره، ثم احفظه في الماستر"
        )

        edited_df = st.data_editor(
            st.session_state["df_working"],
            column_config={
                "REMARKS": st.column_config.TextColumn(
                    "الصنف (بحث أو جديد)",
                    suggestions=master_names,
                    width="large"
                ),
                "Unit_Price": st.column_config.NumberColumn(
                    "السعر",
                    format="%.2f",
                    min_value=0.0
                ),
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="stable_editor"
        )

        if st.button("💾 اعتماد وحفظ"):
            new_rows = []
            master_df_fresh, master_names_fresh = load_master_safe()

            for _, row in edited_df.iterrows():
                name = str(row["REMARKS"]).strip()
                price = float(row["Unit_Price"])

                if name and name not in master_names_fresh:
                    new_rows.append({
                        m_item: name,
                        m_price: price
                    })
                    master_names_fresh.append(name)

            if new_rows:
                updated_master = pd.concat(
                    [master_df_fresh, pd.DataFrame(new_rows)],
                    ignore_index=True
                )
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_rows)} صنف جديد في الماستر")

            edited_df[c_qty] = pd.to_numeric(
                edited_df[c_qty],
                errors="coerce"
            ).fillna(0)

            edited_df["Total"] = (
                edited_df[c_qty] * edited_df["Unit_Price"]
            )

            st.dataframe(edited_df, use_container_width=True)
            st.metric(
                "الإجمالي النهائي",
                f"{edited_df['Total'].sum():,.2f}"
            )

