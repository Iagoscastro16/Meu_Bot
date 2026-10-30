import os
import sqlite3
from contextlib import closing

# banco na raiz do projeto, não importa de onde o bot foi iniciado
CAMINHO_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memoria.db")

def _conectar():
    conexao = sqlite3.connect(CAMINHO_DB)
    conexao.execute(
        "CREATE TABLE IF NOT EXISTS mensagens ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "papel TEXT NOT NULL, "
        "conteudo TEXT NOT NULL, "
        "criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    return conexao

# devolve as últimas mensagens, da mais antiga para a mais nova (formato que a IA espera)
def ultimas(quantidade: int) -> list[dict]:
    with closing(_conectar()) as conexao:
        linhas = conexao.execute(
            "SELECT papel, conteudo FROM mensagens ORDER BY id DESC LIMIT ?",
            (quantidade,),
        ).fetchall()
    return [{"role": papel, "content": conteudo} for papel, conteudo in reversed(linhas)]

# grava a pergunta e a resposta juntas: ou entram as duas, ou nenhuma
def salvar(pergunta: str, resposta: str):
    with closing(_conectar()) as conexao, conexao:
        conexao.executemany(
            "INSERT INTO mensagens (papel, conteudo) VALUES (?, ?)",
            [("user", pergunta), ("assistant", resposta)],
        )
