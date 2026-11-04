# A senha nunca sai deste model, exceto em buscar_credenciais_por_email (uso do login).
COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


class UsuarioModel:
    def __init__(self, database):
        self._database = database

    def listar(self, limit=None, offset=0):
        query = f"SELECT {COLUNAS_PUBLICAS} FROM usuarios ORDER BY id"
        params = []
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        rows = self._database.connection().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._database.connection().execute(
            f"SELECT {COLUNAS_PUBLICAS} FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return dict(row) if row else None

    def buscar_credenciais_por_email(self, email):
        rows = self._database.connection().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id", (email,)
        ).fetchall()
        return [dict(row) for row in rows]

    def criar(self, nome, email, senha_hash, tipo="cliente"):
        with self._database.transacao() as conn:
            return conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            ).lastrowid

    def atualizar_senha(self, usuario_id, senha_hash):
        with self._database.transacao() as conn:
            conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))

    def contar(self):
        return self._database.connection().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
