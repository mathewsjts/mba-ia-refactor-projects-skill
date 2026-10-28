"""Acesso a dados de usuários — SQL parametrizado (T01).

`senha` é lida internamente para verificação no login, mas nunca é serializada
para o cliente (T13 / BC-04) — a view usa um serializer sem o campo.
"""


class UsuarioModel:
    def __init__(self, database):
        self._database = database

    def _conn(self):
        return self._database.connection()

    def listar(self, limit=None, offset=0):
        query = "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios ORDER BY id"
        params = []
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        rows = self._conn().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def contar(self):
        return self._conn().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    def buscar_por_id(self, usuario_id):
        row = self._conn().execute(
            "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return dict(row) if row else None

    def buscar_por_email(self, email):
        row = self._conn().execute(
            "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
        return dict(row) if row else None

    def criar(self, nome, email, senha_hash, tipo="cliente"):
        conn = self._conn()
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        conn.commit()
        return cursor.lastrowid
