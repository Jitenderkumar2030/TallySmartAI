import streamlit as st
import jwt
import pandas as pd
import io
import os
from datetime import datetime
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Backend imports
from backend.chat_advisor import get_financial_advice
from backend.telegram_alert import send_forecast_alert
from backend.cashfree import create_subscription_session
from backend.audit_logger import audit_logger

# AI modules
from ai_modules.fingpt_assistant import ask_fingpt
from ai_modules.finrl_agent import train_agent, get_finrl_recommendation
from ai_modules.trend_analyzer import analyze_financial_trends
from backend.client_manager import client_manager
import plotly.express as px
import plotly.graph_objects as go
from ai_modules.gst_analyzer import gst_detector
from ai_modules.voice_assistant import voice_assistant
from ai_modules.pdf_parser import pdf_parser
import speech_recognition as sr

# --- UI & Auth ---
st.set_page_config(page_title="Dashboard - TallySmartAI", layout="wide")
st.title("📊 TallySmartAI Dashboard")

# Check session token
token = st.session_state.get("token")
if not token:
    st.warning("🔐 Please login to access the dashboard.")
    st.stop()

# Decode token
try:
    payload = jwt.decode(token, "testsecret", algorithms=["HS256"])
except:
    st.error("❌ Invalid or expired token.")
    st.session_state.clear()
    st.stop()

# Welcome and Logout
st.success(f"Welcome {payload['email']}! Role: `{payload['role']}`")

if st.button("🚪 Logout"):
    st.session_state.clear()
    st.success("Logged out successfully. Please refresh.")
    st.stop()

# --- Role-based access handling ---
if payload["role"] == "free":
    st.warning("🆓 You are using the Free Plan – Upgrade to Pro for full features!")

    # Show Upgrade to Pro before CSV upload
    if st.button("💳 Upgrade to Pro"):
        sub_url = create_subscription_session(payload["email"])
        if sub_url:
            st.markdown(f"[👉 Click here to Upgrade]({sub_url})", unsafe_allow_html=True)
        else:
            st.error("❌ Failed to generate payment link.")

# Log dashboard access
audit_logger.log_action(
    user_email=payload["email"],
    action="dashboard_access",
    details={"role": payload["role"], "timestamp": datetime.now().isoformat()}
)

# --- CSV Upload ---
st.subheader("📁 Upload Your Tally CSV")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if not uploaded_file:
    st.info("📤 Please upload your Tally CSV to continue.")
    st.stop()

# Read uploaded CSV
df_uploaded = pd.read_csv(uploaded_file)
st.dataframe(df_uploaded.head())

# Client Selection/Creation
st.subheader("👥 Client Management")
    
user_clients = client_manager.get_user_clients(payload["email"])
    
if len(user_clients) > 0:
    selected_client = st.selectbox(
        "Select Client", 
        options=user_clients['client_code'].tolist(),
        format_func=lambda x: user_clients[user_clients['client_code']==x]['client_name'].iloc[0]
    )
else:
    selected_client = None
    
# Add new client option
with st.expander("➕ Add New Client"):
    new_client_name = st.text_input("Client Name")
    new_client_industry = st.selectbox("Industry", ["Manufacturing", "Trading", "Services", "Retail", "Other"])
    
    if st.button("Add Client"):
        if new_client_name:
            client_code = client_manager.add_client(payload["email"], new_client_name, new_client_industry)
            if client_code:
                st.success(f"✅ Client added: {client_code}")
                client_manager.log_client_data(client_code, "CSV", uploaded_file.name)
                st.rerun()
            else:
                st.error("❌ Failed to add client")

# Smart Trend Analysis (Available for all users)
st.subheader("📊 Smart Trend Analysis")
    
try:
    analysis_result = analyze_financial_trends(df_uploaded)
        
    # Display insights
    for insight in analysis_result['insights']:
        if "📈" in insight:
            st.success(insight)
        elif "📉" in insight or "⚠️" in insight:
            st.warning(insight)
        else:
            st.info(insight)
        
    # Trend metrics
    trends = analysis_result['trends']
    col1, col2, col3 = st.columns(3)
        
    with col1:
        st.metric("Growth Rate", f"{trends.get('avg_growth_rate', 0):.2%}")
    with col2:
        st.metric("Volatility", f"{trends.get('volatility', 0):.2f}")
    with col3:
        st.metric("Pattern", trends.get('seasonal_pattern', 'Unknown'))
        
    # Anomaly Detection
    anomalies = analysis_result['anomalies']
    if anomalies:
        st.subheader("🚨 Anomaly Alerts")
        for anomaly in anomalies[:5]:  # Show top 5
            severity_color = "🔴" if anomaly['severity'] == 'high' else "🟡"
            st.warning(f"{severity_color} Unusual amount: ₹{anomaly['amount']:,.2f} on {anomaly['date']}")

except Exception as e:
    st.error(f"❌ Trend analysis error: {e}")

# Enhanced Visualization
if 'Date' in df_uploaded.columns and 'Amount' in df_uploaded.columns:
    st.subheader("📈 Financial Trends Visualization")
        
    # Prepare data for plotting
    df_plot = df_uploaded.copy()
    df_plot['Date'] = pd.to_datetime(df_plot['Date'])
    monthly_data = df_plot.groupby(df_plot['Date'].dt.to_period('M'))['Amount'].sum().reset_index()
    monthly_data['Date'] = monthly_data['Date'].dt.to_timestamp()
        
    # Create interactive plot
    fig = px.line(monthly_data, x='Date', y='Amount', 
                 title='Monthly Financial Trend',
                 labels={'Amount': 'Amount (₹)', 'Date': 'Month'})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- Free Plan Section ---
if payload["role"] == "free":
    st.markdown("### 🔍 Summary")
    st.metric("🔢 Total Transactions", len(df_uploaded))
    st.metric("💰 Total Revenue", f"₹ {df_uploaded['Amount'].sum():,.2f}")
    st.metric("🏆 Top Ledger", df_uploaded['Ledger'].value_counts().idxmax())

    # Revenue by Ledger Pie Chart
    st.subheader("🍰 Revenue by Ledger")
    ledger_totals = df_uploaded.groupby("Ledger")["Amount"].sum()
    st.pyplot(ledger_totals.plot.pie(autopct="%1.1f%%", figsize=(6, 6)).figure)

    # Monthly Revenue Trend
    try:
        df_uploaded["Date"] = pd.to_datetime(df_uploaded["Date"])
        monthly = df_uploaded.groupby(df_uploaded["Date"].dt.to_period("M"))["Amount"].sum().reset_index()
        monthly["Date"] = monthly["Date"].astype(str)
        st.subheader("📈 Monthly Revenue Trend")
        st.line_chart(monthly.set_index("Date")["Amount"])
    except:
        st.warning("⚠️ Could not generate monthly trend. Check your date format.")

# --- Pro/Admin Plan Section ---
if payload["role"] in ["pro", "admin"]:
    st.success("🎉 You have access to all Pro features!")

    # 1. Ask AI Advisor
    st.subheader("🧠 Ask an AI Financial Advisor")
    advisor_choice = st.radio("Select Advisor", ["TallySmartAI GPT Advisor", "FinGPT AI Analyst"])
    question = st.text_area("Ask a financial/business/tax question:")

    if st.button("Ask Advisor"):
        try:
            if advisor_choice == "TallySmartAI GPT Advisor":
                answer = get_financial_advice(question)
            else:
                answer = ask_fingpt(question)
            st.success(answer)
        except Exception as e:
            st.error(f"❌ AI error: {e}")

    # 2. Forecasting
    st.subheader("📈 AI Forecast Based on Uploaded CSV")
    try:
        files = {"file": uploaded_file.getvalue()}
        r = requests.post(
            "http://localhost:8000/predict",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )

        if r.status_code == 200:
            forecast_df = pd.DataFrame(r.json())
            st.success("✅ Forecast Ready")
            st.dataframe(forecast_df)
            st.line_chart(forecast_df.set_index("ds")["yhat"])

            # CSV Download
            st.download_button("📥 Download CSV", forecast_df.to_csv(index=False), "forecast.csv")

            # Excel Download
            excel_io = io.BytesIO()
            with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
                forecast_df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", excel_io.getvalue(), "forecast.xlsx")

            # PDF Download
            pdf_io = io.BytesIO()
            c = canvas.Canvas(pdf_io, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, height - 40, "📊 TallySmartAI - Forecast Report")
            c.setFont("Helvetica", 10)
            c.drawString(30, height - 60, f"Generated: {datetime.now()}")
            y = height - 90
            col_width = width / len(forecast_df.columns)
            for i, col in enumerate(forecast_df.columns):
                c.drawString(30 + i * col_width, y, str(col))
            y -= 20
            for row in forecast_df.head(20).values:
                for i, cell in enumerate(row):
                    c.drawString(30 + i * col_width, y, str(cell)[:15])
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50
            c.save()
            pdf_io.seek(0)
            st.download_button("📥 Download PDF", pdf_io, "forecast.pdf", "application/pdf")

            # Telegram Notification
            try:
                send_forecast_alert("your_telegram_user_id", "📊 Forecast completed in TallySmartAI.")
            except:
                st.warning("⚠️ Telegram alert failed.")
        else:
            st.error("❌ Forecast API failed.")
    except Exception as e:
        st.error(f"⚠️ Forecast Error: {e}")

    # 3. FinRL Smart Recommendation
    st.subheader("📊 FinRL Smart Recommendation")
    try:
        model = train_agent(df_uploaded)
        suggestion = get_finrl_recommendation(model, df_uploaded)
        st.success(f"📌 FinRL suggests: **{suggestion}** action for financial optimization.")
    except Exception as e:
        st.error(f"❌ FinRL error: {e}")

# Add audit logging for file uploads
if uploaded_file:
    audit_logger.log_action(
        user_email=payload["email"],
        action="file_upload",
        resource=uploaded_file.name,
        details={"file_size": uploaded_file.size, "file_type": "CSV"}
    )

# Add audit trail viewer for admin users
if payload["role"] == "admin":
    st.subheader("🔍 Audit Trail")
    with st.expander("View Recent Activity"):
        logs = audit_logger.get_user_logs(payload["email"], limit=20)
        if logs:
            log_df = pd.DataFrame(logs, columns=['Action', 'Resource', 'Timestamp', 'Details'])
            st.dataframe(log_df)
        else:
            st.info("No recent activity found")

# Voice Assistant Section
st.subheader("🎤 Voice Assistant")
col_voice1, col_voice2 = st.columns(2)

with col_voice1:
    if st.button("🎙️ Start Voice Commands"):
        if voice_assistant.start_listening():
            st.success("🎤 Voice assistant activated! Say 'TallySmartAI' followed by your command.")
            st.info("Available commands: show dashboard, upload file, generate forecast, ask advisor, show trends, export report")
        else:
            st.warning("Voice assistant is already running")

with col_voice2:
    if st.button("🔇 Stop Voice Commands"):
        voice_assistant.stop_listening()
        st.info("Voice assistant stopped")

# Handle voice commands
if 'voice_command' in st.session_state:
    command = st.session_state['voice_command']
    if command == 'show_dashboard':
        st.success("📊 Dashboard is already displayed")
    elif command == 'upload_file':
        st.info("📁 Please use the file uploader above")
    elif command == 'generate_forecast':
        st.info("📈 Scroll down to the forecasting section")
    elif command == 'show_trends':
        st.info("📊 Trend analysis is shown above")
    elif command == 'export_report':
        st.info("📥 Export options are available in the Pro section")
    
    # Clear the command
    del st.session_state['voice_command']

# PDF Invoice Parser Section
st.subheader("📄 PDF Invoice Parser")
uploaded_pdfs = st.file_uploader("Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_pdfs:
    parsed_invoices = []
    progress_bar = st.progress(0)
    
    for i, pdf_file in enumerate(uploaded_pdfs):
        with st.spinner(f"Parsing {pdf_file.name}..."):
            parsed_data = pdf_parser.parse_pdf_invoice(pdf_file)
            parsed_invoices.append(parsed_data)
        
        progress_bar.progress((i + 1) / len(uploaded_pdfs))
    
    # Convert to DataFrame
    if parsed_invoices:
        invoice_df = pdf_parser.convert_to_dataframe(parsed_invoices)
        
        if not invoice_df.empty:
            st.success(f"✅ Successfully parsed {len(invoice_df)} invoices")
            st.dataframe(invoice_df)
            
            # Validation
            validation_issues = pdf_parser.validate_extracted_data(invoice_df)
            if validation_issues:
                st.warning("⚠️ Data validation issues found:")
                for issue in validation_issues:
                    st.write(f"• {issue}")
            
            # Download parsed data
            csv_data = invoice_df.to_csv(index=False)
            st.download_button("📥 Download Parsed Invoice Data", csv_data, "parsed_invoices.csv")
        else:
            st.error("❌ No valid invoice data could be extracted")

# GST Anomaly Detection (Enhanced)
if uploaded_file:
    st.subheader("🏛️ GST Compliance Analysis")
    
    try:
        # Add sample GST columns if not present (for demo)
        if 'GST_Rate' not in df_uploaded.columns:
            df_uploaded['GST_Rate'] = np.random.choice([0, 5, 12, 18, 28], size=len(df_uploaded))
            df_uploaded['GST_Amount'] = df_uploaded['Amount'] * df_uploaded['GST_Rate'] / 100
            df_uploaded['GSTIN'] = 'SAMPLE_GSTIN_DATA'
        
        gst_report = gst_detector.generate_gst_compliance_report(df_uploaded)
        
        # Display GST metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", gst_report['total_transactions'])
        with col2:
            st.metric("GST Applicable", gst_report['gst_applicable'])
        with col3:
            st.metric("Total GST", f"₹{gst_report['total_gst_collected']:,.2f}")
        with col4:
            st.metric("Compliance Score", f"{gst_report['compliance_score']:.1f}%")
        
        # Display GST anomalies
        anomalies = gst_report['anomalies']
        if anomalies:
            st.subheader("🚨 GST Compliance Issues")
            
            for anomaly in anomalies[:10]:  # Show top 10
                severity_color = "🔴" if anomaly['severity'] == 'high' else "🟡"
                with st.expander(f"{severity_color} {anomaly['type'].replace('_', ' ').title()}"):
                    st.write(f"**Issue:** {anomaly['message']}")
                    st.write(f"**Suggestion:** {anomaly['suggestion']}")
                    st.write(f"**Row:** {anomaly['row_index']}")
        else:
            st.success("✅ No GST compliance issues detected")
    
    except Exception as e:
        st.error(f"❌ GST analysis error: {e}")
