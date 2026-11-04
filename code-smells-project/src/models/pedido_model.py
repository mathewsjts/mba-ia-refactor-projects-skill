from src.errors import RegraNegocioError

_SELECT_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(pr.nome, 'Desconhecido') AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar_itens(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


class PedidoModel:
    def __init__(self, database):
        self._database = database

    def criar(self, usuario_id, itens, total):
        """Grava pedido, itens e baixa de estoque numa única transação.

        `itens` chega do service já validado, com `nome` e `preco_unitario` de cada produto.
        A baixa de estoque é condicional (`AND estoque >= ?`): se outra requisição consumiu
        o estoque depois da checagem do service, nenhuma linha é afetada, o mesmo erro de
        negócio é levantado e a transação desfaz o pedido e os itens já gravados.
        """
        with self._database.transacao() as conn:
            pedido_id = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            ).lastrowid
            for item in itens:
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
                atualizado = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if atualizado == 0:
                    raise RegraNegocioError("Estoque insuficiente para " + item["nome"])
        return pedido_id

    def listar(self, limit=None, offset=0):
        if limit is None:
            query = _SELECT_COM_ITENS + " ORDER BY p.id, i.id"
            params = []
        else:
            query = (
                _SELECT_COM_ITENS
                + " WHERE p.id IN (SELECT id FROM pedidos ORDER BY id LIMIT ? OFFSET ?)"
                + " ORDER BY p.id, i.id"
            )
            params = [limit, offset]
        return _agrupar_itens(self._database.connection().execute(query, params).fetchall())

    def listar_por_usuario(self, usuario_id):
        rows = self._database.connection().execute(
            _SELECT_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
        ).fetchall()
        return _agrupar_itens(rows)

    def atualizar_status(self, pedido_id, status):
        with self._database.transacao() as conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def totais(self):
        row = self._database.connection().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   SUM(total) AS faturamento,
                   SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
                   SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
                   SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
            FROM pedidos
            """
        ).fetchone()
        return {
            "total_pedidos": row["total_pedidos"],
            "faturamento": row["faturamento"] if row["faturamento"] is not None else 0,
            "pendentes": row["pendentes"] or 0,
            "aprovados": row["aprovados"] or 0,
            "cancelados": row["cancelados"] or 0,
        }

    def contar(self):
        return self._database.connection().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
