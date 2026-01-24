import streamlit as st
import hashlib

# ---- Simple in-memory users (later we can move to DB) ----
USERS = {
    "admin": "admin123",   # change later
}

# Hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Prepare hashed users
HASHED_USERS = {u: hash_password(p) for u, p in USERS.items()}


def login_form():
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in HASHED_USERS:
            if hash_password(password) == HASHED_USERS[username]:
                st.session_state["authenticated"] = True
                st.session_state["user"] = username
                st.success("✅ Logged in successfully")
                st.rerun()
            else:
                st.error("❌ Wrong password")
        else:
            st.error("❌ User not found")


def logout_button():
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()


def require_login():
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()
