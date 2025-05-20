import os
import telebot
from flask import Flask, request
import openai

# Инициализация переменных
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENAI_TOKEN = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_TOKEN
app = Flask(__name__)

# Установка webhook прямо здесь
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# Обработка обновлений от Telegram
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": message.text}
        ]
    )
    reply = response.choices[0].message['content']
    bot.send_message(message.chat.id, reply)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
