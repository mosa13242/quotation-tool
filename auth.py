import streamlit as st
import hashlib

# ================================
# USERS (غيرهم براحتك)
# ================================

USERS = {
    "admin": "admin123",
    "sales": "1234",
}

# ================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

HASHED_USERS = {u: hash_password(p) for u, p in USERS.items()}


# ================================
def require_login():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:

        st.title("🔐 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            if username in HASHED_USERS and hash_password(password) == HASHED_USERS[username]:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("❌ Wrong username or password")

        st.stop()


# ================================
def logout_button():

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
