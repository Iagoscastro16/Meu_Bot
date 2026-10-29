from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.error import InvalidToken
from openai import AsyncOpenAI,APIConnectionError,APITimeoutError,RateLimitError,AuthenticationError,APIStatusError,InternalServerError
import asyncio
import os
import sys
from dotenv import dotenv_values

# chama as variaveis de ambiente
if not os.path.exists(".env"):
    sys.exit("Arquivo .env não encontrado. Crie o .env na pasta do bot.")

config = dotenv_values(".env")

# confere se todas as chaves existem e não estão vazias
chaves = ["TELEGRAM_TOKEN", "freellmapi", "id_user_telegram"]
faltando = [chave for chave in chaves if not config.get(chave)]
if faltando:
    sys.exit(f"Faltando no .env (ou vazio): {', '.join(faltando)}")

token = config["TELEGRAM_TOKEN"]

token_free= config["freellmapi"]

try:
    meu_id = int(config["id_user_telegram"])
except ValueError:
    sys.exit("id_user_telegram no .env precisa ser um número.")

#chamar o cliente da open ia para o freellm

client = AsyncOpenAI(base_url="http://localhost:3001/v1",api_key=(token_free))

# Função que faz a comunicação

async def ecoar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # verificação se quem está enviando a mensagem sou eu mesmo
    if update.effective_user.id != meu_id:
        print(f"Mensagem ignorada de {update.effective_user.id}")
        return

    texto = update.message.text
    
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        r = await client.chat.completions.create(
            model="auto:fast",
            messages=[{"role": "user", "content": texto}],
            timeout=60,
        )
    except APITimeoutError:
        await update.message.reply_text("A IA demorou demais. Tenta de novo.")
        return

    except APIConnectionError:
        await update.message.reply_text("O serviço de IA está fora do ar.")
        return

    except RateLimitError:
        await update.message.reply_text("Limite de uso atingido. Tenta daqui a pouco.")
        return

    except AuthenticationError:
        print("Chave do FreeLLMAPI inválida, confere o .env")
        await update.message.reply_text("Erro de configuração do bot.")
        return

    except InternalServerError:
        await update.message.reply_text("A IA deu erro do lado dela. Tenta de novo.")
        return

    except Exception as e:
        print(f"Erro inesperado: {e}")
        await update.message.reply_text("Algo deu errado.")
        return

    resposta = r.choices[0].message.content
    if not resposta or not resposta.strip():
        await update.message.reply_text("A IA não devolveu texto. Tenta de novo.")
        return

    await update.message.reply_text(resposta.strip())
# dizer para o python onde pegar as informações 

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ecoar))

try:
    app.run_polling()
except InvalidToken:
    sys.exit("TELEGRAM_TOKEN inválido, confere o .env")