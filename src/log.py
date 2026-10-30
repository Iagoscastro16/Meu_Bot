import logging
import os
import sqlite3
import time
from contextlib import closing, contextmanager
from contextvars import ContextVar
from datetime import datetime
from zoneinfo import ZoneInfo
from config import segredos

# horário de Brasília (o servidor está em UTC, então não dá para confiar no fuso do sistema)
FUSO = ZoneInfo("America/Sao_Paulo")

# formatter que troca qualquer segredo por *** na linha final (inclui tracebacks)
class FormatterSeguro(logging.Formatter):
    # faz o %(asctime)s do terminal usar o fuso de Brasília também
    def converter(self, timestamp):
        return datetime.fromtimestamp(timestamp, FUSO).timetuple()

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

# banco na raiz do projeto, não importa de onde o bot foi iniciado
CAMINHO_DB_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs.db")

FORMATO_DATA = "%Y-%m-%d %H:%M:%S"

# requisicoes: uma linha por mensagem recebida (resumo)
# eventos: uma linha por coisa que o bot logou durante a requisição
def _conectar():
    conexao = sqlite3.connect(CAMINHO_DB_LOG)
    conexao.executescript(
        "CREATE TABLE IF NOT EXISTS requisicoes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "criada_em TEXT NOT NULL, "
        "resultado TEXT NOT NULL, "
        "duracao_ms INTEGER, "
        "modelo TEXT);"
        "CREATE TABLE IF NOT EXISTS eventos ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "requisicao_id INTEGER NOT NULL REFERENCES requisicoes(id), "
        "criada_em TEXT NOT NULL, "
        "nivel TEXT NOT NULL, "
        "mensagem TEXT NOT NULL);"
        "CREATE INDEX IF NOT EXISTS idx_eventos_requisicao ON eventos(requisicao_id);"
    )
    return conexao

# id da requisição em andamento; fora de uma requisição fica None
requisicao_atual: ContextVar[int | None] = ContextVar("requisicao_atual", default=None)

class HandlerSQLite(logging.Handler):
    def emit(self, record):
        requisicao_id = requisicao_atual.get()
        if requisicao_id is None:
            return  # log fora de uma requisição só aparece no terminal

        try:
            with closing(_conectar()) as conexao, conexao:
                conexao.execute(
                    "INSERT INTO eventos (requisicao_id, criada_em, nivel, mensagem) VALUES (?, ?, ?, ?)",
                    (
                        requisicao_id,
                        datetime.fromtimestamp(record.created, FUSO).strftime(FORMATO_DATA),
                        record.levelname,
                        self.format(record),
                    ),
                )
        except Exception:
            self.handleError(record)

# só a mensagem (e o traceback, se tiver); data e nível já têm coluna própria
handler_sqlite = HandlerSQLite()
handler_sqlite.setFormatter(FormatterSeguro("%(message)s"))
logger.addHandler(handler_sqlite)

class Requisicao:
    def __init__(self, id):
        self.id = id
        # se o bot quebrar antes de definir o resultado, fica registrado como "excecao"
        self.resultado = "excecao"
        # modelo que respondeu; fica vazio se a IA não chegou a responder
        self.modelo = None

@contextmanager
def log_da_requisicao():
    # tudo que for logado dentro do "with" vai para o banco ligado a esta requisição
    # (um problema no banco de log nunca pode derrubar o bot, só aparece no terminal)
    inicio = time.monotonic()

    try:
        with closing(_conectar()) as conexao, conexao:
            cursor = conexao.execute(
                "INSERT INTO requisicoes (criada_em, resultado) VALUES (?, ?)",
                (datetime.now(FUSO).strftime(FORMATO_DATA), "em_andamento"),
            )
            requisicao = Requisicao(cursor.lastrowid)
    except Exception:
        logger.exception("Não consegui abrir a requisição no banco de log")
        requisicao = Requisicao(None)

    marca = requisicao_atual.set(requisicao.id)
    try:
        yield requisicao
    finally:
        requisicao_atual.reset(marca)
        if requisicao.id is not None:
            try:
                with closing(_conectar()) as conexao, conexao:
                    conexao.execute(
                        "UPDATE requisicoes SET resultado = ?, duracao_ms = ?, modelo = ? WHERE id = ?",
                        (requisicao.resultado, int((time.monotonic() - inicio) * 1000), requisicao.modelo, requisicao.id),
                    )
            except Exception:
                logger.exception("Não consegui fechar a requisição no banco de log")
