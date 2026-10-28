"""Acesso a dados de produtos — SQL parametrizado (T01)."""

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


class ProdutoModel:
    def __init__(self, database):
        self._database = database

    def _conn(self):
        return self._database.connection()

    def listar(self, limit=None, offset=0):
        query = f"SELECT {COLUNAS} FROM produtos ORDER BY id"
        params = []
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        rows = self._conn().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def contar(self):
        return self._conn().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]

    def buscar_por_id(self, produto_id):
        row = self._conn().execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return dict(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        conn = self._conn()
        cursor = conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        conn.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conn = self._conn()
        conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, "
            "estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        conn.commit()
        return True

    def deletar(self, produto_id):
        conn = self._conn()
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conn.commit()
        return True

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        query = f"SELECT {COLUNAS} FROM produtos WHERE 1=1"
        params = []
        # Preserva a semântica original: `if termo:` ignora string vazia; `if preco_min:` ignora 0.
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = self._conn().execute(query, params).fetchall()
        return [dict(row) for row in rows]
