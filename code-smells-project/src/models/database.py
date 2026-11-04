import sqlite3
from contextlib import contextmanager

from flask import g

from src.models.passwords import hash_password

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER REFERENCES usuarios(id),
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        produto_id INTEGER REFERENCES produtos(id),
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

PRODUTOS_EXEMPLO = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

# Contas de demonstração: só criadas fora de produção (ver Database.inicializar).
USUARIOS_EXEMPLO = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


class Database:
    def __init__(self, path):
        self._path = path

    def connection(self):
        if "db_connection" not in g:
            # isolation_level=None: autocommit fora de transacao(), que controla BEGIN/COMMIT.
            conn = sqlite3.connect(self._path, timeout=10, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db_connection = conn
        return g.db_connection

    def close(self, _exc=None):
        conn = g.pop("db_connection", None)
        if conn is not None:
            conn.close()

    @contextmanager
    def transacao(self):
        """BEGIN IMMEDIATE ... COMMIT; ROLLBACK se qualquer exceção escapar do bloco."""
        conn = self.connection()
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")

    def inicializar(self, com_usuarios_exemplo):
        """Cria o schema e popula o banco vazio, como o original fazia no primeiro acesso."""
        with self.transacao() as conn:
            for ddl in SCHEMA:
                conn.execute(ddl)
            if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
                return

        # Hash fora da transação: o KDF é lento de propósito e não deve segurar o lock do banco.
        usuarios = [
            (nome, email, hash_password(senha), tipo)
            for nome, email, senha, tipo in USUARIOS_EXEMPLO
        ] if com_usuarios_exemplo else []

        with self.transacao() as conn:
            if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                    PRODUTOS_EXEMPLO,
                )
                conn.executemany(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    usuarios,
                )
