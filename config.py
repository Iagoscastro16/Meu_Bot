import os
import sys
from dotenv import dotenv_values

# procura o .env na pasta deste arquivo, não importa de onde o bot foi iniciado
CAMINHO_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# chama as variaveis de ambiente
if not os.path.exists(CAMINHO_ENV):
    sys.exit("Arquivo .env não encontrado. Crie o .env na pasta do bot.")

_config = dotenv_values(CAMINHO_ENV)

# confere se todas as chaves existem e não estão vazias
_chaves = ["TELEGRAM_TOKEN", "freellmapi", "id_user_telegram"]
_faltando = [chave for chave in _chaves if not _config.get(chave)]
if _faltando:
    sys.exit(f"Faltando no .env (ou vazio): {', '.join(_faltando)}")

token = _config["TELEGRAM_TOKEN"]

token_free = _config["freellmapi"]

try:
    meu_id = int(_config["id_user_telegram"])
except ValueError:
    sys.exit("id_user_telegram no .env precisa ser um número.")

# valores que nunca podem aparecer nos logs
segredos = [token, token_free]
