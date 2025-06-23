import streamlit as st
from backend.auth_service import create_user
from streamlit_extras.switch_page_button import switch_page  # Make sure this is installed

st.set_page_config(page_title="Sign Up - TallySmartAI")

st.title("📝 Create an Account")

email = st.text_input("Email")
pw = st.text_input("Password", type="password")
role = st.selectbox("Choose Role", ["free", "pro"])

if st.button("Sign up"):
    try:
        success = create_user(email, pw, role)
        if success:
            st.success("✅ Account created successfully! Redirecting to Login...")
            st.rerun()  # Refresh session
            switch_page("Login")  # This must match your Login.py page name without `.py`
        else:
            st.error("❌ Signup failed. Try again.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

