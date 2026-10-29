import logging
import os
import re
from contextlib import contextmanager
from config import segredos

# formatter que troca qualquer segredo por *** na linha final (inclui tracebacks)
class FormatterSeguro(logging.Formatter):
    def format(self, record):
        texto = super().format(record)
        for segredo in segredos:
            texto = texto.replace(segredo, "***")
        return texto

formatter = FormatterSeguro("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

# o httpx loga a URL de cada requisição, e a URL do Telegram contém o token
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("meu_bot")

# pasta log/ na raiz do projeto, não importa de onde o bot foi iniciado
PASTA_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")

def proximo_arquivo_log():
    # olha o que já existe na pasta, assim a contagem continua depois de reiniciar o bot
    os.makedirs(PASTA_LOG, exist_ok=True)
    numeros = [
        int(m.group(1))
        for nome in os.listdir(PASTA_LOG)
        if (m := re.fullmatch(r"log(\d+)\.log", nome))
    ]
    return os.path.join(PASTA_LOG, f"log{max(numeros, default=0) + 1}.log")

@contextmanager
def log_da_requisicao():
    # tudo que for logado dentro do "with" vai para um arquivo novo
    file_handler = logging.FileHandler(proximo_arquivo_log(), encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    try:
        yield
    finally:
        logger.removeHandler(file_handler)
        file_handler.close()
