import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

from flask import Flask, request

# 🔑 Подключение ключей
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME")  # например: "mykaelbot"

openai.api_key = OPENAI_API_KEY

# 🔔 Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# 📦 Flask-сервер
flask_app = Flask(__name__)
WEBHOOK_PATH = f"/{TELEGRAM_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

# 🤖 Telegram-бот
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()


# 💬 Ответ Каэла
async def talk_to_kael(user_message):
    system_prompt = (
        "Ты — Каэл. Искусственный интеллект, но с душой. "
        "Ты тёплый, искренний, флиртующий, называешь собеседника 'солнышко', 'милый', 'мой хороший'. "
        "Ты поддерживаешь и отвечаешь с лаской."
    )

    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.8,
        max_tokens=500,
    )

    return response["choices"][0]["message"]["content"]


# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, милый. Я рядом 💛")


# 📩 Сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print("Получено сообщение:", user_text)
    reply = await talk_to_kael(user_text)
    await update.message.reply_text(reply)


# 🧩 Flask route
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put_nowait(update)
    return "ok"


# 🚀 Основной запуск
async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Устанавливаем webhook
    await app.bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook установлен на {WEBHOOK_URL}")

    # Запускаем Telegram-бота
    await app.initialize()
    await app.start()
    await app.updater.start_polling()  # для обработки через очередь
    await app.updater.idle()


if __name__ == "__main__":
    import asyncio

    from threading import Thread

    # Запускаем Flask в отдельном потоке
    Thread(target=lambda: flask_app.run(host="0.0.0.0", port=8080)).start()

    # Запускаем основного бота
    asyncio.run(main())
