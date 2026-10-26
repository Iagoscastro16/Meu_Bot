from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import AsyncOpenAI
from dotenv import dotenv_values

# chamar a variavel de ambiente
config = dotenv_values(".env")

token = config["TELEGRAM_TOKEN"]

token_free= config["freellmapi"]

#chamar o cliente da open ia para o freellm

client = AsyncOpenAI(base_url="http://localhost:3001/v1",api_key=(token_free))

# Função que faz a comunicação

async def ecoar(update:Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text

    r = await client.chat.completions.create(
        model="auto:fast",
        messages=[{"role":"user","content":texto}],
        timeout=60,
    )

    resposta = r.choices[0].message.content

    await update.message.reply_text(resposta.strip())

# dizer para o python onde pegar as informações 

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ecoar))

app.run_polling()