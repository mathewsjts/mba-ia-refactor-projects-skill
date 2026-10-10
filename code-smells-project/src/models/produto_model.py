"""Acesso a dados de produtos — SQL parametrizado (T01)."""

_COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


class ProdutoModel:
    def __init__(self, database):
        self._database = database

    def listar(self, limit=None, offset=0):
        query = f"SELECT {_COLUNAS} FROM produtos"
        params = []
        if limit is not None:
            query += " ORDER BY id LIMIT ? OFFSET ?"
            params = [limit, offset]
        rows = self._database.connection().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._database.connection().execute(
            f"SELECT {_COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return dict(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        cursor = self._database.connection().execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        self._database.connection().commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        self._database.connection().execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        self._database.connection().commit()

    def deletar(self, produto_id):
        self._database.connection().execute(
            "DELETE FROM produtos WHERE id = ?", (produto_id,)
        )
        self._database.connection().commit()

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        query = f"SELECT {_COLUNAS} FROM produtos WHERE 1=1"
        params = []
        # Preserva a semântica de truthiness do original (`if termo:`, `if preco_min:`).
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
        rows = self._database.connection().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def contar(self):
        return self._database.connection().execute(
            "SELECT COUNT(*) FROM produtos"
        ).fetchone()[0]
