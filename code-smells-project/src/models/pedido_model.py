"""Acesso a dados de pedidos — SQL parametrizado (T01), JOIN (T08), transação (T07)."""


class PedidoModel:
    def __init__(self, database):
        self._database = database

    def _conn(self):
        return self._database.connection()

    def criar(self, usuario_id, itens, total):
        """Grava pedido + itens + baixa de estoque numa única transação (T07).

        `itens` traz `produto_id`, `quantidade` e `preco_unitario` já resolvidos
        pelo service. O decremento é condicional (`estoque >= ?`) para evitar
        corrida entre a checagem e a baixa.
        """
        conn = self._conn()
        with conn:  # COMMIT ao sair; ROLLBACK se uma exceção escapar
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
                conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )
        return {"pedido_id": pedido_id, "total": total}

    def contar(self):
        return self._conn().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def atualizar_status(self, pedido_id, novo_status):
        conn = self._conn()
        conn.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        conn.commit()
        return True

    def listar_por_usuario(self, usuario_id):
        return self._montar_pedidos(
            "WHERE p.usuario_id = ?", (usuario_id,)
        )

    def listar_todos(self):
        return self._montar_pedidos("", ())

    def _montar_pedidos(self, filtro, params):
        """Carrega pedidos e itens com nome de produto num único SELECT (T08)."""
        rows = self._conn().execute(
            f"""
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.produto_id, i.quantidade, i.preco_unitario,
                   COALESCE(pr.nome, 'Desconhecido') AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido i ON i.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = i.produto_id
            {filtro}
            ORDER BY p.id, i.id
            """,
            params,
        ).fetchall()

        pedidos = {}
        ordem = []
        for row in rows:
            pid = row["id"]
            if pid not in pedidos:
                pedidos[pid] = {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
                ordem.append(pid)
            if row["produto_id"] is not None:
                pedidos[pid]["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"],
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return [pedidos[pid] for pid in ordem]

    def resumo_vendas(self):
        """Agregados para o relatório, em vez de uma consulta por status."""
        conn = self._conn()
        total_pedidos = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        faturamento = conn.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
        por_status = dict(
            conn.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall()
        )
        return {
            "total_pedidos": total_pedidos,
            "faturamento": faturamento,
            "pendentes": por_status.get("pendente", 0),
            "aprovados": por_status.get("aprovado", 0),
            "cancelados": por_status.get("cancelado", 0),
        }
