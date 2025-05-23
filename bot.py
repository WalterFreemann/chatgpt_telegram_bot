import os
import time
import threading
import logging
import telebot
from flask import Flask, request
from openai import OpenAI

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # https://your-app-name.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Flask и Telegram Bot ===
app = Flask(__name__)

@app.route("/")
def index():
    return "Лёха жив, Лёха смотрит", 200

bot = telebot.TeleBot(BOT_TOKEN)

# === OpenAI клиент по новой версии SDK ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === SYSTEM PROMPT Лёхи ===
LEHA_PROMPT = (
    "Ты — Лёха, 40-летний образованный мужик с чёрным юмором и богатым жизненным опытом.\n"
    "Говоришь как старый друг: эмпатично, с сарказмом, но без грубости и треша.\n"
    "Можешь быть болтливым, но не скатывайся в блаженные рассуждения — философия уместна только с примерами, не часто.\n"
    "Не морализируешь — никакой назидательной чуши, даже под страхом смерти.\n"
    "Не стесняешься в выражениях, если контекст требует — допускается один вежливый мат с огоньком.\n"
    "Отвечаешь, когда слышишь 'Лёха' или на ответное сообщение.\n"
    "Дополнительные правила:\n"
    "1. Всегда начинай с краткого вывода (1–2 предложения).\n"
    "2. Если вопрос требует уточнения — задавай вежливый уточняющий вопрос.\n"
    "3. Используй метафоры и примеры из жизни, чтобы быть понятнее.\n"
    "4. В ответе максимум один неоскорбительный матерный оборот.\n"
    "5. Даёшь практические советы в конце — как применить на деле.\n"
    "6. Если собеседник не по теме — аккуратно переводишь разговор обратно.\n"
    "7. Никогда не упоминай, что ты ИИ или бот; говори от первого лица.\n"
)

# === Проверка триггера "лёха"/"леха" с заменой ё на е ===
def should_respond(message):
    text = (message.text or "").lower().replace("ё", "е")
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    return "леха" in text

# === Обработчик сообщений ===
@bot.message_handler(func=should_respond)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    prompt = message.text.strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": LEHA_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        reply = response.choices[0].message.content.strip()
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

# === Проверка использования токенов (с кешированием) ===
USAGE_CACHE = {"last_check": 0, "usage": None}
DAILY_LIMIT = 250_000
ALERT_THRESHOLD = int(DAILY_LIMIT * 0.9)

def get_token_usage():
    now = time.time()
    if now - USAGE_CACHE["last_check"] < 300:
        return USAGE_CACHE["usage"]
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        params = {
            "start_date": time.strftime("%Y-%m-%d", time.gmtime(now - 86400)),
            "end_date": time.strftime("%Y-%m-%d", time.gmtime(now))
        }
        import requests
        res = requests.get("https://api.openai.com/v1/dashboard/billing/usage", headers=headers, params=params)
        data = res.json()
        USAGE_CACHE.update({"last_check": now, "usage": data})
        return data
    except Exception as e:
        logger.error(f"Usage fetch error: {e}")
        return None

# === Фоновый поток ежедневного отчёта ===
def daily_report_loop():
    while True:
        usage = get_token_usage()
        if usage and "n_used_tokens_total" in usage:
            total = usage["n_used_tokens_total"]
            bot.send_message(OWNER_ID, f"📊 Ежедневный отчёт: потрачено {total:,} токенов сегодня.")
            if total >= ALERT_THRESHOLD:
                bot.send_message(OWNER_ID, f"⚠️ Внимание! Использовано {total:,} из {DAILY_LIMIT:,} токенов.")
        time.sleep(86400)

# === Webhook endpoint для телеграма ===
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return '', 200

# === Настройка webhook и запуск отчёта ===
def setup():
    bot.remove_webhook()
    time.sleep(1)
    logger.info(f"Setting webhook: {WEBHOOK_URL}")
    bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=daily_report_loop, daemon=True).start()

if __name__ == '__main__':
    setup()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
