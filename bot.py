from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import AsyncOpenAI,APIConnectionError,APITimeoutError,RateLimitError,AuthenticationError,APIStatusError
import asyncio
from dotenv import dotenv_values

# chamar a variavel de ambiente
config = dotenv_values(".env")

token = config["TELEGRAM_TOKEN"]

token_free= config["freellmapi"]

#chamar o cliente da open ia para o freellm

client = AsyncOpenAI(base_url="http://localhost:3001/v1",api_key=(token_free))

# Função que faz a comunicação

async def ecoar(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

app.run_polling()