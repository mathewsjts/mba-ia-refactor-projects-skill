"""Acesso a dados de usuários — SQL parametrizado (T01).

A senha nunca é devolvida nas listagens públicas; `buscar_por_email` retorna o hash
apenas para a verificação de login feita em código (T05).
"""


class UsuarioModel:
    def __init__(self, database):
        self._database = database

    def listar(self):
        rows = self._database.connection().execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios"
        ).fetchall()
        return [dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._database.connection().execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return dict(row) if row else None

    def buscar_por_email(self, email):
        row = self._database.connection().execute(
            "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
        return dict(row) if row else None

    def criar(self, nome, email, senha_hash, tipo="cliente"):
        cursor = self._database.connection().execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        self._database.connection().commit()
        return cursor.lastrowid

    def contar(self):
        return self._database.connection().execute(
            "SELECT COUNT(*) FROM usuarios"
        ).fetchone()[0]
