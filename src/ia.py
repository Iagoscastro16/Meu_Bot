from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError, InternalServerError
from config import token_free
from src.log import logger

#chamar o cliente da open ia para o freellm

client = AsyncOpenAI(base_url="http://localhost:3001/v1", api_key=token_free)

# manda a pergunta para a IA e devolve o texto que vai para o usuário
# (a resposta da IA, ou uma mensagem amigável se algo der errado)

async def perguntar(texto: str) -> str:
    try:
        r = await client.chat.completions.create(
            model="auto:fast",
            messages=[{"role": "user", "content": texto}],
            timeout=60,
        )
    except APITimeoutError:
        logger.warning("Timeout na chamada da IA")
        return "A IA demorou demais. Tenta de novo."

    except APIConnectionError:
        logger.error("Não conectou no serviço de IA")
        return "O serviço de IA está fora do ar."

    except RateLimitError:
        logger.warning("Limite de uso da IA atingido")
        return "Limite de uso atingido. Tenta daqui a pouco."

    except AuthenticationError:
        logger.error("Chave do FreeLLMAPI inválida, confere o .env")
        return "Erro de configuração do bot."

    except InternalServerError:
        logger.error("Erro interno do lado da IA")
        return "A IA deu erro do lado dela. Tenta de novo."

    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return "Algo deu errado."

    resposta = r.choices[0].message.content
    if not resposta or not resposta.strip():
        logger.warning("A IA devolveu resposta vazia")
        return "A IA não devolveu texto. Tenta de novo."

    return resposta.strip()
