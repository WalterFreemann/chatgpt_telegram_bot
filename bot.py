import os
import telebot
from flask import Flask, request
import openai

# Инициализация переменных из environment
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENAI_TOKEN = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_TOKEN
app = Flask(__name__)

# Установка webhook (удаляем старый и ставим новый)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

# Команда /start — приветствие
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот Леха. Чтобы я ответил, упомяни моё имя — 'Леха'.")

# Команда /help — помощь
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Я бот Леха — общаюсь через ChatGPT.\n"
        "Чтобы получить ответ, напиши сообщение с именем 'Леха'.\n"
        "Пример: 'Леха, расскажи анекдот.'\n"
        "Команды:\n"
        "/start — приветствие\n"
        "/help — эта помощь"
    )
    bot.reply_to(message, help_text)

# Обработка сообщений, в которых есть слово "леха"
@bot.message_handler(func=lambda message: 'леха' in message.text.lower())
def handle_message(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )
        reply = response.choices[0].message['content']
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        bot.send_message(message.chat.id, "Извини, что-то пошло не так. Попробуй позже.")
        print(f"Error: {e}")

# Все остальные сообщения игнорируем (можешь добавить, если надо)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
