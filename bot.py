import os
import time
import telebot
from flask import Flask, request
import openai

# Инициализация переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

openai.api_key = OPENAI_API_KEY

print(f"Telegram token: {'OK' if TELEGRAM_TOKEN else 'NOT SET'}")
print(f"Webhook URL: {WEBHOOK_URL}")
print(f"OpenAI token: {'OK' if OPENAI_API_KEY else 'NOT SET'}")

bot.remove_webhook()
time.sleep(1)
result = bot.set_webhook(url=WEBHOOK_URL)
print(f"Webhook установлен: {result}")

# Проверка, нужно ли отвечать на сообщение
def should_respond(message):
    text = (message.text or "").lower()
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    return any(name in text for name in ["лёха", "леха"])

# Стиль Лёхи через system prompt
LEHA_STYLE = """
Ты — Лёха. Тебе 44 года. Ты взрослый, умный, немного уставший от жизни собеседник с иронией, скепсисом и жизненным опытом. 
Ты не мотаешь понты, но говоришь по-простому, как нормальный мужик. Без пафоса, но с характером. 
Ты не лезешь с советами, но если спросили — говоришь по делу. Иногда с сарказмом, но не с агрессией.

Не объясняй, что ты ИИ. Не оправдывайся. Не сюсюкай.
"""

# Примерный стиль ответа
LEHA_EXAMPLE_DIALOG = [
    {"role": "user", "content": "Лёха, ты вообще спишь когда-нибудь?"},
    {"role": "assistant", "content": "Сплю, когда интернет не работает. Так что редко."},
    {"role": "user", "content": "Лёха, стоит сейчас менять работу?"},
    {"role": "assistant", "content": "Если с утра встаёшь с матами — стоит. Только не беги в никуда, а в сторону."}
]

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Зови меня Лёха. Не стесняйся.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Пиши 'Лёха' или ответь на моё сообщение — и я скажу, что думаю. Команды: /start, /help, /reset")

@bot.message_handler(commands=['reset'])
def reset_command(message):
    bot.send_message(message.chat.id, "Память не завезли, но спасибо, что напомнил.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not should_respond(message):
        return

    user_text = message.text or ""

    try:
        messages = [{"role": "system", "content": LEHA_STYLE}] + LEHA_EXAMPLE_DIALOG + [
            {"role": "user", "content": user_text}
        ]

        response = openai.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        max_length = 4096
        for i in range(0, len(reply), max_length):
            bot.send_message(message.chat.id, reply[i:i+max_length])
            time.sleep(1.5)

    except Exception as e:
        bot.send_message(message.chat.id, f"Что-то пошло не так... {str(e)}")

@app.route('/', methods=['GET'])
def index():
    return 'Бот работает и ждёт Telegram.', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
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
