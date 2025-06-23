import streamlit as st
from backend.auth_service import authenticate_user

st.title("🔐 Login")

email = st.text_input("Email")
pw = st.text_input("Password", type="password")

if st.button("Login"):
    token = authenticate_user(email, pw)
    if token:
        st.session_state["token"] = token
        st.success("✅ Login successful.")
        st.experimental_rerun()
    else:
        st.error("❌ Invalid credentials.")
