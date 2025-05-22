import os
import time
import datetime
import telebot
import openai
from flask import Flask, request

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ADMIN_CHAT_ID = 258535298
DAILY_TOKEN_LIMIT = 250_000
ALERT_THRESHOLD = int(DAILY_TOKEN_LIMIT * 0.9)

bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
last_report_date = None

def check_token_usage():
    global last_report_date
    try:
        usage = openai.APIUsage.retrieve()
        total = usage['daily_token_usage']['total_tokens']

        # Тревога при приближении к лимиту
        if total > ALERT_THRESHOLD:
            bot.send_message(ADMIN_CHAT_ID, f"⚠️ Почти исчерпан лимит: {total:,} из {DAILY_TOKEN_LIMIT:,} токенов.")

        # Отчёт раз в сутки
        today = datetime.date.today()
        if last_report_date != today:
            last_report_date = today
            bot.send_message(
                ADMIN_CHAT_ID,
                f"📊 Ежедневный отчёт:\nПотрачено токенов: {total:,} из {DAILY_TOKEN_LIMIT:,}"
            )
    except Exception as e:
        print(f"[ERROR] Не удалось получить usage: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Бот отвечает, только если его зовут по имени или на его сообщение отвечают
        if (message.text and 'лёха' in message.text.lower()) or message.reply_to_message and message.reply_to_message.from_user.username == bot.get_me().username:
            bot.send_chat_action(message.chat.id, 'typing')

            # Простая заглушка-ответ
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "Ты умный, саркастичный мужик по имени Лёха. Отвечай по делу, с юмором, но не как пацан, а как взрослый мужик с опытом."},
                    {"role": "user", "content": message.text},
                ]
            )
            bot.send_message(message.chat.id, response.choices[0].message.content)

        # Проверка и отчёт по токенам
        check_token_usage()

    except Exception as e:
        print(f"[ERROR] Ошибка в handle_message: {e}")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok', 200

@app.route('/')
def index():
    return 'Бот работает'

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://chatgpt-telegram-bot-662g.onrender.com/{BOT_TOKEN}")
