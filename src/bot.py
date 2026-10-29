from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.error import InvalidToken
import sys
from config import token, meu_id
from src.log import logger, log_da_requisicao
from src.ia import perguntar

# Função que faz a comunicação

async def ecoar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # verificação se quem está enviando a mensagem sou eu mesmo
    # (mensagens de estranhos não geram arquivo, só aviso no terminal)
    if update.effective_user.id != meu_id:
        logger.warning("Mensagem ignorada de %s", update.effective_user.id)
        return

    # cada requisição ganha o seu próprio arquivo de log
    with log_da_requisicao():
        texto = update.message.text
        logger.info("Mensagem recebida (%d caracteres)", len(texto))

        await update.message.chat.send_action(ChatAction.TYPING)

        resposta = await perguntar(texto)

        await update.message.reply_text(resposta)
        logger.info("Resposta enviada (%d caracteres)", len(resposta))

# dizer para o python onde pegar as informações

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ecoar))

try:
    app.run_polling()
except InvalidToken:
    sys.exit("TELEGRAM_TOKEN inválido, confere o .env")
