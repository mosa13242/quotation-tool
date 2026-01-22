import streamlit as st
import pandas as pd
import os
from thefuzz import fuzz, process

st.set_page_config(page_title="نظام التسعير والتعلم الذكي", layout="wide")

# 1. تحميل وتحديث الماستر ليست
MASTER_FILE = "master_list.xlsx"

def load_master():
    if not os.path.exists(MASTER_FILE):
        df_new = pd.DataFrame(columns=["Item", "Price"])
        df_new.to_excel(MASTER_FILE, index=False)
        return df_new, []
    df = pd.read_excel(MASTER_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df, df[df.columns[0]].astype(str).tolist()

master_df, master_names = load_master()

st.title("🛡️ نظام التسعير (حفظ الاسم والسعر الجديد تلقائياً)")

uploaded_file = st.file_uploader("ارفع طلب العميل (Excel فقط)", type=["xlsx"])

if uploaded_file:
    df_client = pd.read_excel(uploaded_file)
    df_client.columns = [str(c).strip() for c in df_client.columns]
    
    c1, c2 = st.columns(2)
    with c1:
        c_item = st.selectbox("عمود الصنف (عندك):", df_client.columns)
        c_qty = st.selectbox("عمود الكمية (عندك):", df_client.columns)
    with c2:
        m_item = st.selectbox("عمود الصنف (في الماستر):", master_df.columns)
        m_price = st.selectbox("عمود السعر (في الماستر):", master_df.columns)

    if st.button("🔍 تنفيذ مطابقة وتحليل"):
        def smart_match(text):
            if not master_names: return str(text)
            match, score = process.extractOne(str(text), master_names, scorer=fuzz.token_set_ratio)
            return match if score > 65 else str(text)

        df_client['REMARKS'] = df_client[c_item].apply(smart_match)
        # سحب الأسعار الحالية للأصناف المطابقة
        price_dict = dict(zip(master_df[m_item], master_df[m_price]))
        df_client['Unit_Price'] = df_client['REMARKS'].map(price_dict).fillna(0)
        st.session_state['df_working'] = df_client

    # --- واجهة الـ EDIT المزدوجة (اسم + سعر) ---
    if 'df_working' in st.session_state:
        st.warning("💡 لتسجيل صنف جديد: اكتب الاسم في REMARKS واكتب سعره في Unit_Price ثم اضغط اعتماد.")
        
        # تم فتح عمود REMARKS وعمود Unit_Price للتعديل
        edited_df = st.data_editor(
            st.session_state['df_working'],
            column_config={
                "REMARKS": st.column_config.TextColumn("الصنف (EDIT)", width="large"),
                "Unit_Price": st.column_config.NumberColumn("السعر (EDIT)", format="%.2f EGP")
            },
            disabled=[c_item, c_qty],
            use_container_width=True,
            key="smart_editor_v3"
        )

        if st.button("🚀 اعتماد التسعير وحفظ البيانات الجديدة"):
            new_entries = []
            current_master_items = master_df[m_item].astype(str).tolist()

            # فحص كل سطر بحثاً عن إضافات جديدة
            for index, row in edited_df.iterrows():
                item_name = str(row['REMARKS']).strip()
                item_price = float(row['Unit_Price'])
                
                # إذا كان الاسم جديداً تماماً أو كان موجوداً ولكن تم تعديل سعره يدوياً
                if item_name not in current_master_items and item_name != "":
                    new_entries.append({m_item: item_name, m_price: item_price})
                    current_master_items.append(item_name)

            # تحديث ملف الماستر فعلياً بالأسماء والأسعار الجديدة
            if new_entries:
                new_df = pd.DataFrame(new_entries)
                updated_master = pd.concat([master_df, new_df], ignore_index=True)
                updated_master.to_excel(MASTER_FILE, index=False)
                st.success(f"✅ تم حفظ {len(new_entries)} صنف جديد مع أسعارهم في الماستر ليست!")

            # حساب الإجماليات النهائية للعرض الحالي
            edited_df[c_qty] = pd.to_numeric(edited_df[c_qty], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df[c_qty] * edited_df['Unit_Price']
            
            st.dataframe(edited_df, use_container_width=True)
            st.metric("الإجمالي النهائي", f"{edited_df['Total'].sum():,.2f} EGP")
            
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل عرض السعر", csv, "Final_Quote.csv", "text/csv")
