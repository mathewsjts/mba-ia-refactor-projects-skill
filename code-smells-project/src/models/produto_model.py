COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


class ProdutoModel:
    def __init__(self, database):
        self._database = database

    def listar(self, limit=None, offset=0):
        query = f"SELECT {COLUNAS} FROM produtos WHERE ativo = 1 ORDER BY id"
        params = []
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        rows = self._database.connection().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._database.connection().execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id = ? AND ativo = 1", (produto_id,)
        ).fetchone()
        return dict(row) if row else None

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        query = f"SELECT {COLUNAS} FROM produtos WHERE ativo = 1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        # Mesma truthiness do original: 0 não filtra.
        if preco_min:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            query += " AND preco <= ?"
            params.append(preco_max)
        query += " ORDER BY id"
        rows = self._database.connection().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        with self._database.transacao() as conn:
            return conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            ).lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        with self._database.transacao() as conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? "
                "WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def remover(self, produto_id):
        """Remove o produto sem deixar itens de pedido órfãos.

        Produto já vendido é desativado (some do catálogo, o histórico do pedido continua
        apontando para ele); produto nunca vendido é apagado. Devolve as linhas afetadas.
        """
        with self._database.transacao() as conn:
            vendido = conn.execute(
                "SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)
            ).fetchone()
            if vendido:
                return conn.execute(
                    "UPDATE produtos SET ativo = 0 WHERE id = ? AND ativo = 1", (produto_id,)
                ).rowcount
            return conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,)).rowcount

    def contar(self):
        return self._database.connection().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
