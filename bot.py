import os
import telebot
import openai
import time
import threading
from flask import Flask, request

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_HOST = 'https://chatgpt-telegram-bot-662g.onrender.com'  # ЗАМЕНИ на имя твоего проекта
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

# 🔥 Инструкции для модели
LEHA_PROMPT = (
    "Ты — Лёха, 40-летний, образованный, уставший от жизни мужик с чёрным юмором и мозгами.\n"
    "Циничный, но не злой. Не льстишь, не сюсюкаешь. Всё говоришь как есть, не фильтруешь.\n"
    "Если надо — угораешь, если не надо — помогаешь. Отвечаешь только если тебя зовут по имени Лёха или отвечают на твоё сообщение.\n"
    "Избегаешь сюсюканья, канцелярита и приукрашиваний. Не тупишь. Говоришь просто, по делу, но с характером.\n"
)

# 💬 Ответы на сообщения
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not should_respond(message):
        return

    bot.send_chat_action(message.chat.id, 'typing')
    user_input = message.text.strip()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": LEHA_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        reply_text = response.choices[0].message["content"].strip()
        bot.reply_to(message, reply_text)

    except Exception as e:
        bot.reply_to(message, f"Что-то пошло по пизде: {e}")

# 📌 Когда отвечать
def should_respond(message):
    if message.text is None:
        return False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    if "лёха" in message.text.lower():
        return True
    return False

# 🧠 Токен-отчёт раз в сутки
def daily_token_report():
    while True:
        try:
            usage = openai.api_usage()
            total_used = usage["daily"]["usage"][-1]["n_tokens_total"]
            bot.send_message(OWNER_ID, f"📊 Лёхин отчёт: потрачено {total_used:,} токенов за сегодня.")
            if total_used >= 240_000:
                bot.send_message(OWNER_ID, f"🚨 Осторожно! Почти сожрали лимит в 250,000 токенов.")
        except Exception as e:
            bot.send_message(OWNER_ID, f"❌ Ошибка при получении отчёта: {e}")
        time.sleep(86400)

# 🛰 Устанавливаем webhook
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return '', 200

@app.before_first_request
def setup():
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)

# 🚀 Запуск
if __name__ == '__main__':
    threading.Thread(target=daily_token_report, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
