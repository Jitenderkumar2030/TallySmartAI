import streamlit as st
from backend.auth_service import create_user

st.title("📝 Create an Account")

email = st.text_input("Email")
pw = st.text_input("Password", type="password")
role = st.selectbox("Choose Role", ["free", "pro"])

if st.button("Sign up"):
    create_user(email, pw, role)
    st.success("✅ User created. Please login from the sidebar.")
