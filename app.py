# app.py
import streamlit as st
from auth_service import create_user, authenticate_user
import jwt
import pandas as pd
import requests
from chat_advisor import get_financial_advice
from models import SessionLocal, User
from auth import hash_password
from telegram_alert import send_forecast_alert
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from cashfree import create_subscription_session

st.set_page_config(page_title="TallySmartAI", page_icon="📊", layout="wide")

# -------------------- Initialize State --------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"

def go_to(page):
    st.session_state.page = page

# -------------------- Sidebar Navigation --------------------
with st.sidebar:
    st.title("🧭 Navigation")

    st.button("🏠 Home", on_click=go_to, args=("landing",))
    st.button("💸 Pricing", on_click=go_to, args=("Pricing",))
    st.button("📖 About Us", on_click=go_to, args=("About Us",))
    st.button("📞 Contact Us", on_click=go_to, args=("Contact Us",))
    st.button("🚀 Careers", on_click=go_to, args=("Careers",))

    st.markdown("---")
    st.button("🔐 Login", on_click=go_to, args=("Login",))
    st.button("📝 Signup", on_click=go_to, args=("Signup",))
    st.button("🔁 Reset Password", on_click=go_to, args=("Reset Password",))

    if "token" in st.session_state:
        st.markdown("---")
        st.button("📊 Dashboard", on_click=go_to, args=("Dashboard",))
        st.button("🚪 Logout", on_click=lambda: st.session_state.clear())

# -------------------- Landing Page --------------------
if st.session_state.page == "landing":
    st.image("https://img.freepik.com/free-vector/data-analysis-landing-page_23-2149550356.jpg", use_container_width=True)
    st.title("📊 Welcome to TallySmartAI")
    st.markdown("""
    ### AI-Powered Forecasting & Financial Advisory Platform
    > Upload Tally CSV. Get instant forecasts, financial insights, and downloadable reports.
    """)
    col1, col2 = st.columns(2)
    with col1:
        st.button("🔐 Login", on_click=go_to, args=("Login",))
    with col2:
        st.button("📝 Signup", on_click=go_to, args=("Signup",))

# -------------------- Signup Page --------------------
elif st.session_state.page == "Signup":
    st.title("📝 Create an Account")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    role = st.selectbox("Choose Role", ["free", "pro"])
    if st.button("Sign up"):
        create_user(email, pw, role)
        st.success("✅ User created. Go to login.")
        st.button("🔐 Go to Login", on_click=go_to, args=("Login",))

# -------------------- Login Page --------------------
elif st.session_state.page == "Login":
    st.title("🔐 Login")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        token = authenticate_user(email, pw)
        if token:
            st.session_state["token"] = token
            st.session_state.page = "Dashboard"
            st.success("✅ Login successful.")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid credentials.")

# -------------------- Reset Password Page --------------------
elif st.session_state.page == "Reset Password":
    st.title("🔁 Reset Password")
    email = st.text_input("Registered Email")
    new_pw = st.text_input("New Password", type="password")
    if st.button("Reset"):
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password = hash_password(new_pw)
            db.commit()
            st.success("✅ Password updated successfully.")
        else:
            st.error("❌ Email not found.")
        db.close()

# -------------------- Pricing Page --------------------
elif st.session_state.page == "Pricing":
    st.title("💸 Pricing Plans")
    st.info("Choose the plan that suits your needs.")
    st.markdown("""
    ### 🔓 Free Plan
    - Forecasting: ❌
    - Advisor: ❌
    - CSV Upload: ✅
    - Price: ₹0/month

    ### 💼 Pro Plan
    - Forecasting: ✅
    - Advisor: ✅
    - Full Dashboard Access: ✅
    - Download Reports: ✅
    - Price: ₹999/month
    """)

# -------------------- About Us Page --------------------
elif st.session_state.page == "About Us":
    st.title("📖 About TallySmartAI")
    st.markdown("""
    **TallySmartAI** is an AI-powered platform to automate financial forecasting,
    empower small businesses, and provide intelligent advisory services.

    - 💡 Founded by innovators in FinTech & AI
    - 🌐 Used by startups, SMEs, and consultants across India
    - 🧠 Driven by GPT-based forecasting & analysis
    """)

# -------------------- Contact Us Page --------------------
elif st.session_state.page == "Contact Us":
    st.title("📞 Get in Touch")
    st.markdown("Have questions? Reach out to us below:")
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    message = st.text_area("Your Message")
    if st.button("Send Message"):
        st.success("✅ Message sent! We'll get back to you soon.")

# -------------------- Careers Page --------------------
elif st.session_state.page == "Careers":
    st.title("🚀 Careers @ TallySmartAI")
    st.markdown("""
    Join a fast-growing AI startup transforming business forecasting in India!

    #### Open Positions:
    - Python Developer (Remote)
    - Data Scientist (Bangalore)
    - React Frontend Intern
    - Marketing Associate

    📧 Email your resume: **careers@tallysmartai.in**
    """)

# -------------------- Dashboard Page --------------------
elif st.session_state.page == "Dashboard":
    st.title("📊 Dashboard")
    token = st.session_state.get("token")

    if not token:
        st.warning("🔐 Please log in.")
    else:
        try:
            payload = jwt.decode(token, "testsecret", algorithms=["HS256"])
        except Exception as e:
            st.error("❌ Invalid or expired token.")
            st.session_state.clear()
            st.stop()

        st.success(f"Welcome {payload['email']}! Role: `{payload['role']}`")

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.success("✅ Logged out.")
            st.session_state.page = "landing"
            st.experimental_rerun()

        # Pro upgrade
        if payload["role"] == "free":
            st.warning("🔓 Upgrade to Pro to unlock full features.")
            if st.button("💳 Generate Payment Link"):
                sub_url = create_subscription_session(payload["email"])
                if sub_url:
                    st.markdown(f"[🔓 Click here to Upgrade to Pro]({sub_url})", unsafe_allow_html=True)
                else:
                    st.error("❌ Failed to create subscription link.")

        # GPT Advisor
        if payload["role"] in ["pro", "admin"]:
            st.subheader("🧠 Ask Financial Advisor")
            question = st.text_area("Ask any business/tax question")
            if st.button("Ask Advisor"):
                try:
                    answer = get_financial_advice(question)
                    st.success(answer)
                except:
                    st.error("❌ GPT service error.")

        # Forecast
        if payload["role"] in ["pro", "admin"]:
            st.subheader("📁 Upload Tally CSV for Forecast")
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
            if uploaded_file:
                files = {"file": uploaded_file.getvalue()}
                r = requests.post(
                    "http://localhost:8000/predict",
                    files=files,
                    headers={"Authorization": f"Bearer {token}"}
                )
                if r.status_code == 200:
                    result = r.json()
                    df = pd.DataFrame(result)
                    st.dataframe(df)
                    st.line_chart(df.set_index("ds")["yhat"])

                    # CSV
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download CSV", csv, "forecast.csv", "text/csv")

                    # Excel
                    excel_io = io.BytesIO()
                    with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name="Forecast")
                    st.download_button("📥 Download Excel", excel_io.getvalue(), "forecast.xlsx")

                    # PDF
                    pdf_io = io.BytesIO()
                    c = canvas.Canvas(pdf_io, pagesize=letter)
                    width, height = letter
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(30, height - 40, "📊 TallySmartAI - Forecast Report")
                    c.setFont("Helvetica", 10)
                    c.drawString(30, height - 60, f"Generated: {datetime.now()}")
                    y = height - 90
                    col_width = width / len(df.columns)
                    for i, col in enumerate(df.columns):
                        c.drawString(30 + i * col_width, y, str(col))
                    y -= 20
                    for row in df.head(20).values:
                        for i, cell in enumerate(row):
                            c.drawString(30 + i * col_width, y, str(cell)[:15])
                        y -= 15
                        if y < 50:
                            c.showPage()
                            y = height - 50
                    c.save()
                    pdf_io.seek(0)
                    st.download_button("📥 Download PDF", pdf_io, "forecast.pdf", "application/pdf")

                    # Telegram
                    try:
                        send_forecast_alert("your_telegram_user_id", "📊 Forecast completed in TallySmartAI.")
                    except:
                        st.warning("⚠️ Telegram alert failed.")
                else:
                    st.error("❌ Prediction failed.")
