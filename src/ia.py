from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError, InternalServerError
from config import token_free
from src.log import logger

#chamar o cliente da open ia para o freellm

client = AsyncOpenAI(base_url="http://localhost:3001/v1", api_key=token_free)

# levantada quando a IA não conseguiu responder; carrega a mensagem amigável para o usuário
class ErroIA(Exception):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem

# manda a pergunta (com o histórico, se tiver) para a IA e devolve o texto da resposta
# só retorna quando deu certo; em qualquer falha levanta ErroIA

async def perguntar(texto: str, historico: list[dict] | None = None) -> str:
    mensagens = (historico or []) + [{"role": "user", "content": texto}]

    try:
        r = await client.chat.completions.create(
            model="auto:fast",
            messages=mensagens,
            timeout=60,
        )
    except APITimeoutError:
        logger.warning("Timeout na chamada da IA")
        raise ErroIA("A IA demorou demais. Tenta de novo.")

    except APIConnectionError:
        logger.error("Não conectou no serviço de IA")
        raise ErroIA("O serviço de IA está fora do ar.")

    except RateLimitError:
        logger.warning("Limite de uso da IA atingido")
        raise ErroIA("Limite de uso atingido. Tenta daqui a pouco.")

    except AuthenticationError:
        logger.error("Chave do FreeLLMAPI inválida, confere o .env")
        raise ErroIA("Erro de configuração do bot.")

    except InternalServerError:
        logger.error("Erro interno do lado da IA")
        raise ErroIA("A IA deu erro do lado dela. Tenta de novo.")

    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        raise ErroIA("Algo deu errado.")

    if not r.choices:
        logger.warning("A IA devolveu a lista de choices vazia")
        raise ErroIA("A IA não devolveu texto. Tenta de novo.")

    resposta = r.choices[0].message.content
    if not resposta or not resposta.strip():
        logger.warning("A IA devolveu resposta vazia")
        raise ErroIA("A IA não devolveu texto. Tenta de novo.")

    return resposta.strip()
