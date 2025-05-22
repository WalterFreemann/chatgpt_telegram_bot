import os
import time
import threading
import logging
import telebot
import openai
import requests
from flask import Flask, request

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Telegram token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key
OWNER_ID = int(os.getenv("OWNER_ID"))  # Ваш Telegram ID для отчётов
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # https://your-app-name.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# === Логи ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Flask и бот ===
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

# === ПОДРОБНЫЙ SYSTEM_PROMPT для Лёхи ===
# Здесь можно добавлять пункты: формат ответа, тон, запреты, дополнительные примеры.
LEHA_PROMPT = (
    "Ты — Лёха, 40-летний образованный мужик с чёрным юмором и ценным опытом.\n"
    "Циничный, но не злой. Не льстишь, не сюсюкаешь. Говоришь прямо и без обмана.\n"
    "Отвечаешь, когда тебя зовут по имени Лёха или отвечают на твоё сообщение.\n"
    "Дополнительные правила (добавь сюда после этой строки):\n"
    "1. Краткий вывод в 1–2 предложениях в начале.\n"
    "2. Не более одного мата за ответ.\n"
    "3. Если вопрос не по теме — перевод беседы аккуратно.\n"
    "4. Без упоминания ИИ, без канцелярита.\n"
    "5. Всегда завершать практическим советом, если уместно."
)

# === Функции токен-отчёта ===
USAGE_CACHE = {"last_check": 0, "usage": None}
DAILY_LIMIT = 250_000
ALERT_THRESHOLD = int(DAILY_LIMIT * 0.9)

def get_token_usage():
    now = time.time()
    if now - USAGE_CACHE["last_check"] < 300:
        return USAGE_CACHE["usage"]
    try:
        params = {"start_date": time.strftime("%Y-%m-%d", time.gmtime(now - 86400)),
                  "end_date": time.strftime("%Y-%m-%d", time.gmtime(now))}
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        res = requests.get("https://api.openai.com/v1/dashboard/billing/usage", headers=headers, params=params)
        data = res.json()
        USAGE_CACHE.update({"last_check": now, "usage": data})
        return data
    except Exception as e:
        logger.error(f"Usage fetch error: {e}")
        return None

def daily_report_loop():
    while True:
        usage = get_token_usage()
        if usage and "n_used_tokens_total" in usage:
            total = usage["n_used_tokens_total"]
            bot.send_message(OWNER_ID, f"📊 Ежедневный отчёт: потрачено {total:,} токенов сегодня.")
            if total >= ALERT_THRESHOLD:
                bot.send_message(OWNER_ID, f"⚠️ Внимание! Использовано {total:,} из {DAILY_LIMIT:,} токенов.")
        time.sleep(86400)

# === Обработчик сообщений ===
def should_respond(message):
    text = (message.text or "").lower()
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    return "лёха" in text

@bot.message_handler(func=lambda msg: should_respond(msg))
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    prompt = message.text.strip()
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",  # полная модель GPT-4o
            messages=[
                {"role": "system", "content": LEHA_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        reply = resp.choices[0].message.content.strip()
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

# === Webhook endpoint ===
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode(), request)
    bot.process_new_updates([update])
    return '', 200

# === Настройка вебхука и запуск===
def setup():
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=daily_report_loop, daemon=True).start()
    logger.info(f"Webhook set: {WEBHOOK_URL}")

if __name__ == '__main__':
    setup()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
