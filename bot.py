import os
import time
import telebot
from flask import Flask, request
import openai

# Инициализация токенов
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENAI_TOKEN = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_TOKEN
app = Flask(__name__)

# Установка webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# Webhook обработка
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

# Команды
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Зови меня просто — Лёха. Спро́сишь — отвечу, если не тупой вопрос :)")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Просто пиши сообщение с моим именем — 'Лёха', и я отвечу. Есть ещё команды: /start, /help, /reset")

@bot.message_handler(commands=['reset'])
def reset_command(message):
    bot.send_message(message.chat.id, "Чистить пока нечего, я ж без памяти как рыбка 🐟")

# Главный хендлер
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if 'лёха' not in message.text.lower():
        return

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Ты — Лёха. Умный, дерзкий ироничный собеседник, говоришь просто, по-уличному, но не грубишь без причины."},
                {"role": "user", "content": message.text}
            ]
        )
        reply = response.choices[0].message['content']

        # Отправка с паузами если текст слишком длинный
        max_length = 4096
        parts = [reply[i:i+max_length] for i in range(0, len(reply), max_length)]
        for part in parts:
            bot.send_message(message.chat.id, part)
            time.sleep(1.5)  # пауза между частями

    except Exception as e:
        bot.send_message(message.chat.id, f"Что-то пошло не так, братишка... {str(e)}")

@app.route('/', methods=['GET'])
def index():
    return 'Бот жив и ждёт POST-запросов от Telegram 🤖', 200

# Запуск Flask-приложения
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
