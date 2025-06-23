import streamlit as st
import jwt
import pandas as pd
import io
from datetime import datetime
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from backend.chat_advisor import get_financial_advice
from backend.telegram_alert import send_forecast_alert
from backend.cashfree import create_subscription_session

st.set_page_config(page_title="Dashboard - TallySmartAI", layout="wide")

st.title("📊 TallySmartAI Dashboard")

# Token Check
token = st.session_state.get("token")
if not token:
    st.warning("🔐 Please login to access the dashboard.")
    st.stop()

try:
    payload = jwt.decode(token, "testsecret", algorithms=["HS256"])
except:
    st.error("❌ Invalid or expired token.")
    st.session_state.clear()
    st.stop()

st.success(f"Welcome {payload['email']}! Role: `{payload['role']}`")

# Upgrade prompt for Free Users
if payload["role"] == "free":
    st.warning("🔓 Upgrade to Pro to unlock full features.")
    if st.button("💳 Generate Payment Link"):
        sub_url = create_subscription_session(payload["email"])
        if sub_url:
            st.markdown(f"[Click here to Upgrade to Pro]({sub_url})", unsafe_allow_html=True)
        else:
            st.error("❌ Failed to create subscription link.")

# Only Pro/Admin gets full features
if payload["role"] in ["pro", "admin"]:
    st.subheader("🧠 Ask Financial Advisor")
    question = st.text_area("Ask any business/tax question:")
    if st.button("Ask Advisor"):
        try:
            answer = get_financial_advice(question)
            st.success(answer)
        except:
            st.error("❌ GPT service error.")

    st.subheader("📁 Upload Tally CSV for Forecast & Insights")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        st.info("📄 Preview of Uploaded Data:")
        st.dataframe(df_uploaded.head())

        try:
            # Send to AI Prediction API
            files = {"file": uploaded_file.getvalue()}
            r = requests.post(
                "http://localhost:8000/predict",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )

            if r.status_code == 200:
                result = r.json()
                df = pd.DataFrame(result)
                st.success("✅ AI Forecast Ready")
                st.dataframe(df)

                st.line_chart(df.set_index("ds")["yhat"])

                # Downloads
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, "forecast.csv", "text/csv")

                excel_io = io.BytesIO()
                with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Forecast")
                st.download_button("📥 Download Excel", excel_io.getvalue(), "forecast.xlsx")

                # PDF Generation
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

                try:
                    send_forecast_alert("your_telegram_user_id", "📊 Forecast completed in TallySmartAI.")
                except:
                    st.warning("⚠️ Telegram alert failed.")

            else:
                st.error("❌ Prediction failed from server.")

        except Exception as e:
            st.error(f"⚠️ AI API call failed: {e}")
            st.markdown("### 🧪 Showing Dummy Insights")
            # Fallback: show dummy summary
            st.metric("Total Transactions", len(df_uploaded))
            st.metric("Total Revenue", f"₹ {df_uploaded['Amount'].sum():,.2f}")
            st.metric("Top Ledger", df_uploaded['Ledger'].value_counts().idxmax())

            st.bar_chart(df_uploaded.groupby("Ledger")["Amount"].sum())

    else:
        st.info("📤 Please upload your Tally CSV to get started.")
