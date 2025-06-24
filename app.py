# app.py (main Streamlit app)

import streamlit as st

st.set_page_config(page_title="TallySmartAI", page_icon="📊", layout="wide")

# Optional Redirect Handler
page = st.session_state.get("page")
if page == "login":
    st.session_state["page"] = None
    st.switch_page("pages/Login.py")  # Ensure this page exists
elif page == "dashboard":
    st.session_state["page"] = None
    st.switch_page("pages/Dashboard.py")

# Sidebar
with st.sidebar:
    st.title("🧭 Navigation")
    st.markdown("Navigate using the sidebar or use buttons below 👇")

# Landing Page
st.title("📊 Welcome to TallySmartAI")

st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://images.pexels.com/photos/7876971/pexels-photo-7876971.jpeg" style="width: 800px; height: auto;">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
### AI-Powered Forecasting & Financial Advisory Platform  
> Upload Tally CSV. Get instant forecasts, financial insights, and downloadable reports.
""")

# Login / Signup Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🔐 Login", use_container_width=True):
        st.session_state["page"] = "login"
        st.rerun()
with col2:
    if st.button("📝 Signup", use_container_width=True):
        st.session_state["page"] = "signup"
        st.switch_page("pages/Signup.py")  # Adjust path as needed

# Features
st.markdown("### 🔍 Explore More")

col_feat, col_review = st.columns(2)

with col_feat:
    st.subheader("🚀 Why TallySmartAI?")
    st.markdown("""
- 📈 **Instant Financial Forecasting**  
- 🤖 **AI-powered Business Insights**  
- 🧾 **Auto-generated Reports & Analysis**  
- 🔒 **End-to-End Data Security**  
- 🌐 **Access Anywhere, Anytime**
""")

with col_review:
    st.subheader("💬 What Our Users Say")
    st.success("“TallySmartAI saved us hours of manual effort each week. The insights are spot on!” – Priya, CFO at RetailNest")
    st.info("“Seamless integration and excellent support. Game-changer for small businesses.” – Rohan, Founder of GreenMart")
    st.warning("“Loved the reports and visual insights. Helped us make faster decisions.” – Meena, Head of Finance at FinBridge")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 10px; font-size: 14px;'>
    © 2025 <strong>TallySmartAI</strong> | Built with ❤️ by Jitender Kumar  
    <br>Need help? <a href="/7_Contact_Us" target="_self">📞 Contact Support</a>
</div>
""", unsafe_allow_html=True)

