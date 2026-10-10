"""Conexão, schema e seed (T11, T15).

Sem estado global mutável: a conexão vive no contexto da requisição (flask.g) e é
fechada no teardown. O schema declara foreign keys e a conexão ativa
`PRAGMA foreign_keys = ON` para garantir integridade referencial.
"""
import sqlite3

from flask import g

from src.models.passwords import hash_password

# Seed de desenvolvimento: usuários e produtos de exemplo criados no primeiro boot
# (o original fazia o mesmo). As senhas são gravadas com hash; as credenciais abaixo
# servem apenas ao ambiente de exemplo/desenvolvimento.
_SEED_PRODUTOS = [
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
]
_SEED_USUARIOS = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


class Database:
    def __init__(self, path):
        self._path = path

    def connection(self):
        if "db_connection" not in g:
            conn = sqlite3.connect(self._path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db_connection = conn
        return g.db_connection

    def close(self, _exc=None):
        conn = g.pop("db_connection", None)
        if conn is not None:
            conn.close()

    def setup(self):
        """Cria o schema e popula o seed se o banco estiver vazio (idempotente)."""
        conn = self.connection()
        conn.executescript(
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
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT,
                senha TEXT,
                tipo TEXT DEFAULT 'cliente',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER REFERENCES usuarios(id),
                status TEXT DEFAULT 'pendente',
                total REAL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS itens_pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER REFERENCES pedidos(id),
                produto_id INTEGER REFERENCES produtos(id),
                quantidade INTEGER,
                preco_unitario REAL
            );
            """
        )
        conn.commit()

        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
                "VALUES (?, ?, ?, ?, ?)",
                _SEED_PRODUTOS,
            )
            conn.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                [(nome, email, hash_password(senha), tipo)
                 for nome, email, senha, tipo in _SEED_USUARIOS],
            )
            conn.commit()
