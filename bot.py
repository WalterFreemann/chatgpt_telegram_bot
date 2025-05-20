import os
from flask import Flask, request
import telebot
import openai

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например, https://chatgpt-telegram-bot.onrender.com

bot = telebot.TeleBot(API_TOKEN)
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# Устанавливаем webhook
@app.before_first_request
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

@app.route('/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне любой текст, и я отвечу с помощью ChatGPT.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=message.text,
            max_tokens=150,
            temperature=0.7,
        )
        answer = response.choices[0].text.strip()
        bot.send_message(message.chat.id, answer)
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обращении к OpenAI API.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
