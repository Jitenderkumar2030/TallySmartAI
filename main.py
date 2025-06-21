# main.py
from nicegui import ui, app
from auth_service import create_user, authenticate_user
from auth import hash_password
from models import SessionLocal, User
import requests
import jwt
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from telegram_alert import send_forecast_alert
from chat_advisor import get_financial_advice
from cashfree import create_subscription_session

# Session storage
user_session = {'token': None, 'payload': None}

@ui.page("/")
def home():
    with ui.card():
        ui.label("Welcome to TallySmartAI").classes("text-2xl font-bold")
        ui.button("Login", on_click=lambda: ui.open("/login"))
        ui.button("Signup", on_click=lambda: ui.open("/signup"))
        ui.button("Reset Password", on_click=lambda: ui.open("/reset"))

@ui.page("/signup")
def signup():
    with ui.card():
        ui.label("Create an Account").classes("text-xl")
        email = ui.input("Email")
        pw = ui.input("Password", password=True)
        role = ui.select(["free", "pro"], label="Role")
        
        def handle_signup():
            create_user(email.value, pw.value, role.value)
            ui.notify("User created! Go to login.")
            ui.open("/login")

        ui.button("Sign up", on_click=handle_signup)

@ui.page("/login")
def login():
    with ui.card():
        ui.label("Login").classes("text-xl")
        email = ui.input("Email")
        pw = ui.input("Password", password=True)

        def handle_login():
            token = authenticate_user(email.value, pw.value)
            if token:
                user_session['token'] = token
                user_session['payload'] = jwt.decode(token, "testsecret", algorithms=["HS256"])
                ui.open("/dashboard")
            else:
                ui.notify("Invalid credentials")

        ui.button("Login", on_click=handle_login)

@ui.page("/reset")
def reset_password():
    with ui.card():
        ui.label("Reset Password").classes("text-xl")
        email = ui.input("Registered Email")
        new_pw = ui.input("New Password", password=True)

        def handle_reset():
            db = SessionLocal()
            user = db.query(User).filter(User.email == email.value).first()
            if user:
                user.password = hash_password(new_pw.value)
                db.commit()
                ui.notify("Password updated!")
            else:
                ui.notify("Email not found.")
            db.close()

        ui.button("Reset Password", on_click=handle_reset)

@ui.page("/dashboard")
def dashboard():
    if not user_session['token']:
        ui.notify("Please login first.")
        ui.open("/login")
        return

    payload = user_session['payload']
    ui.label(f"📊 Welcome {payload['email']}! Role: {payload['role']}").classes("text-xl")

    ui.button("Logout", on_click=lambda: logout())

    if payload['role'] == 'free':
        ui.notify("Upgrade to Pro to unlock all features")

        def upgrade():
            sub_url = create_subscription_session(payload['email'])
            if sub_url:
                ui.open(sub_url)
            else:
                ui.notify("Payment link generation failed")

        ui.button("💳 Upgrade to Pro", on_click=upgrade)

    if payload['role'] in ['pro', 'admin']:
        ui.label("🧠 Ask Financial Advisor")
        question = ui.input("Ask any business/tax question")

        def ask():
            try:
                answer = get_financial_advice(question.value)
                ui.notify(answer)
            except:
                ui.notify("GPT service error")

        ui.button("Ask Advisor", on_click=ask)

    if payload['role'] in ['pro', 'admin']:
        ui.label("📁 Upload Tally CSV for Forecast")

        def handle_upload(file):
            if file:
                content = file.read()
                files = {"file": content}
                r = requests.post("http://localhost:8000/predict", files=files,
                                  headers={"Authorization": f"Bearer {user_session['token']}"})
                if r.status_code == 200:
                    df = pd.DataFrame(r.json())
                    ui.table.from_pandas(df)
                    
                    # CSV
                    csv = df.to_csv(index=False).encode("utf-8")
                    ui.download(text=csv.decode(), filename="forecast.csv")

                    # Excel
                    excel_io = io.BytesIO()
                    with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False)
                    ui.download(content=excel_io.getvalue(), filename="forecast.xlsx")

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
                    ui.download(content=pdf_io.read(), filename="forecast.pdf")

                    try:
                        send_forecast_alert("your_telegram_user_id", "📊 Forecast completed in TallySmartAI.")
                    except:
                        ui.notify("Telegram alert failed")
                else:
                    ui.notify("Prediction failed")

        ui.upload(on_upload=handle_upload)


def logout():
    user_session.clear()
    ui.notify("Logged out")
    ui.open("/")

if __name__ == '__main__':
    print("✅ Server is up and running.")
    ui.run(reload=True, port=8080)
