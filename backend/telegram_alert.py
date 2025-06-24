from telegram import Bot
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_forecast_alert(user_id, message):
    bot.send_message(chat_id=user_id, text=message)
