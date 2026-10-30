from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.error import InvalidToken
import sys
from config import token, meu_id
from src.log import logger, log_da_requisicao
from src.ia import perguntar, ErroIA, MODELO
from src.memoria import ultimas, salvar

# quantas mensagens anteriores (pergunta + resposta contam como 2) vão para a IA
MENSAGENS_NA_MEMORIA = 20

# Função que faz a comunicação

async def ecoar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # verificação se quem está enviando a mensagem sou eu mesmo
    # (mensagens de estranhos não geram registro, só aviso no terminal)
    if update.effective_user.id != meu_id:
        logger.warning("Mensagem ignorada de %s", update.effective_user.id)
        return

    # cada requisição ganha o seu registro no banco de log
    with log_da_requisicao(MODELO) as requisicao:
        texto = update.message.text
        logger.info("Mensagem recebida (%d caracteres)", len(texto))

        await update.message.chat.send_action(ChatAction.TYPING)

        try:
            resposta = await perguntar(texto, ultimas(MENSAGENS_NA_MEMORIA))
        except ErroIA as erro:
            # deu errado: avisa o usuário e não grava nada na memória
            requisicao.resultado = erro.tipo
            await update.message.reply_text(erro.mensagem)
            return

        await update.message.reply_text(resposta)
        requisicao.resultado = "sucesso"
        logger.info("Resposta enviada (%d caracteres)", len(resposta))

        # deu certo e o usuário recebeu: agora sim grava
        try:
            salvar(texto, resposta)
        except Exception as e:
            logger.exception("Não consegui gravar na memória: %s", e)

# dizer para o python onde pegar as informações

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ecoar))

try:
    app.run_polling()
except InvalidToken:
    sys.exit("TELEGRAM_TOKEN inválido, confere o .env")
