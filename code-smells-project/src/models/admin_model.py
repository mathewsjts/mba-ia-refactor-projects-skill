"""Acesso a dados das operações administrativas.

As rotas que usam este model são protegidas por token de administrador (T14).
`executar_query` continua sendo uma operação perigosa: mantida por contrato, mas
restrita à credencial administrativa.
"""


class AdminModel:
    def __init__(self, database):
        self._database = database

    def resetar(self):
        conn = self._database.connection()
        with conn:  # as quatro remoções numa única transação
            conn.execute("DELETE FROM itens_pedido")
            conn.execute("DELETE FROM pedidos")
            conn.execute("DELETE FROM produtos")
            conn.execute("DELETE FROM usuarios")

    def executar_query(self, sql):
        """Executa SQL bruto. Retorna (is_select, linhas)."""
        conn = self._database.connection()
        cursor = conn.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return True, [dict(row) for row in cursor.fetchall()]
        conn.commit()
        return False, None
