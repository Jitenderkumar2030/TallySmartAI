# telegram_alert.py
from telegram import Bot

TELEGRAM_BOT_TOKEN = "your_bot_token_here"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_forecast_alert(chat_id, message):
    bot.send_message(chat_id=chat_id, text=message)
