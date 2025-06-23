# streamlit_app.py
import streamlit as st

st.set_page_config(page_title="TallySmartAI", page_icon="📊", layout="wide")

# Sidebar Navigation (Do NOT use st.page_link here)
with st.sidebar:
    st.title("🧭 Navigation")
    st.markdown("Navigate using sidebar or use links below 👇")

# Landing Page Content
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
    st.link_button("🔐 Login", url="/1_Login", use_container_width=True)
with col2:
    st.link_button("📝 Signup", url="/2_Signup", use_container_width=True)

# Features & Testimonials in Columns
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
footer = """
<div style='text-align: center; padding: 10px; font-size: 14px;'>
    © 2025 <strong>TallySmartAI</strong> | Built with ❤️ using Streamlit  
    <br>Need help? <a href="/7_Contact_Us" target="_self">📞 Contact Support</a>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
