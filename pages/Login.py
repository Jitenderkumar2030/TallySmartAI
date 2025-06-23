import streamlit as st
import jwt
from streamlit_extras.switch_page_button import switch_page  # Install via pip if not present

st.set_page_config(page_title="Login - TallySmartAI", layout="centered")

# Login Form
st.title("🔐 Login to TallySmartAI")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    # Simulate backend auth – replace this with real API call
    if email and password:
        # Simulate role fetch from backend
        if email.endswith("pro.com"):
            role = "pro"
        else:
            role = "free"

        # Encode JWT and store in session
        token = jwt.encode({"email": email, "role": role}, "testsecret", algorithm="HS256")
        st.session_state["token"] = token

        # Redirect based on role
        if role == "pro":
            switch_page("Dashboard")  # Default dashboard is already role-aware
        else:
            switch_page("Dashboard")  # Same page, logic inside handles free/pro separation
    else:
        st.error("❌ Enter email and password.")
