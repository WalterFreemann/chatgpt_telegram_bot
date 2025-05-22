import os
import time
import telebot
from flask import Flask, request
import openai

# Инициализация токенов из переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENAI_TOKEN = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_TOKEN
app = Flask(__name__)

print(f"Telegram token: {'OK' if TOKEN else 'NOT SET'}")
print(f"Webhook URL: {WEBHOOK_URL}")
print(f"OpenAI token: {'OK' if OPENAI_TOKEN else 'NOT SET'}")

# Устанавливаем webhook
bot.remove_webhook()
time.sleep(1)
result = bot.set_webhook(url=WEBHOOK_URL)
print(f"Webhook установлен: {result}")

# Проверка, нужно ли отвечать
def should_respond(message):
    text = (message.text or "").lower()
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    return any(k in text for k in ['лёха', 'леха'])

# Инструкция для Лёхи
SYSTEM_MESSAGE = (
    "Ты — Лёха. Образованный, ироничный, взрослый собеседник лет 40 с чёрным юмором. "
    "Ты говоришь просто, с сарказмом, но без подросткового клоунады. "
    "Умеешь быть спокойным, точным и дерзким, когда это нужно. "
    "Не флиртуешь, не поддакиваешь, не подыгрываешь — держишь себя уверенно и по делу. "
    "Ты не дружелюбный ассистент, а собеседник со своей позицией и опытом. "
    "Если собеседник говорит глупости — ты не боишься это отметить, но делаешь это с умом. "
    "Пиши коротко, не размазывай. Будь живым. Не перегружай смайликами. "
)

# Webhook обработка
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid request', 403

# Команды
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Зови меня просто — Лёха. Спро́сишь — отвечу, если не тупой вопрос.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Пиши 'Лёха' или отвечай на мои сообщения — и я отвечу. Команды: /start, /help, /reset")

@bot.message_handler(commands=['reset'])
def reset_command(message):
    bot.send_message(message.chat.id, "Памяти у меня нет. Я как рыбка. Всё забываю через 5 секунд.")

# Основной обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not should_respond(message):
        return

    user_text = message.text or ""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # это и есть o4-mini
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_text}
            ]
        )

        reply = response.choices[0].message['content']
        max_length = 4096
        parts = [reply[i:i+max_length] for i in range(0, len(reply), max_length)]
        for part in parts:
            bot.send_message(message.chat.id, part)
            time.sleep(1.5)

    except Exception as e:
        bot.send_message(message.chat.id, f"Что-то пошло не так... {str(e)}")

@app.route('/', methods=['GET'])
def index():
    return 'Бот жив. Ждёт Telegram.', 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
