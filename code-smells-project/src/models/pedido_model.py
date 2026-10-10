"""Acesso a dados de pedidos — SQL parametrizado (T01), escrita transacional (T07)
e leitura com JOIN em vez de N+1 (T08)."""


class PedidoModel:
    def __init__(self, database):
        self._database = database

    def criar(self, usuario_id, itens, total):
        """Insere o pedido, seus itens e dá baixa no estoque numa única transação.

        `itens` é uma lista de dicts {produto_id, quantidade, preco_unitario} já
        validada pela camada de serviço.
        """
        conn = self._database.connection()
        with conn:  # COMMIT ao sair; ROLLBACK se uma exceção escapar
            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            )
            pedido_id = cursor.lastrowid
            for item in itens:
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
                conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )
        return {"pedido_id": pedido_id, "total": total}

    def listar_com_itens(self, usuario_id=None):
        query = (
            "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em, "
            "       i.produto_id, i.quantidade, i.preco_unitario, "
            "       COALESCE(pr.nome, 'Desconhecido') AS produto_nome "
            "FROM pedidos p "
            "LEFT JOIN itens_pedido i ON i.pedido_id = p.id "
            "LEFT JOIN produtos pr ON pr.id = i.produto_id"
        )
        params = []
        if usuario_id is not None:
            query += " WHERE p.usuario_id = ?"
            params.append(usuario_id)
        query += " ORDER BY p.id, i.id"

        pedidos = {}
        ordem = []
        for row in self._database.connection().execute(query, params).fetchall():
            if row["id"] not in pedidos:
                pedidos[row["id"]] = {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
                ordem.append(row["id"])
            if row["produto_id"] is not None:
                pedidos[row["id"]]["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"],
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return [pedidos[pid] for pid in ordem]

    def atualizar_status(self, pedido_id, novo_status):
        self._database.connection().execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        self._database.connection().commit()

    def resumo_vendas(self):
        conn = self._database.connection()
        total = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(total), 0) AS faturamento FROM pedidos"
        ).fetchone()
        por_status = {
            row["status"]: row["c"]
            for row in conn.execute(
                "SELECT status, COUNT(*) AS c FROM pedidos GROUP BY status"
            ).fetchall()
        }
        return {
            "total_pedidos": total["total"],
            "faturamento": total["faturamento"],
            "pendentes": por_status.get("pendente", 0),
            "aprovados": por_status.get("aprovado", 0),
            "cancelados": por_status.get("cancelado", 0),
        }

    def contar(self):
        return self._database.connection().execute(
            "SELECT COUNT(*) FROM pedidos"
        ).fetchone()[0]
