import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import dotenv_values

config = dotenv_values(".env")

token = config["TELEGRAM_TOKEN"]



async def ecoar(update:Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text

    await update.message.reply_text(texto)

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ecoar))

app.run_polling()