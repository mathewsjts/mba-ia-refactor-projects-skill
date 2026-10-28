"""Reset de dados para uso local — exposto só como comando de linha (T14).

A rota HTTP /admin/reset-db foi removida (BC-02): destruição em massa não deve
ser alcançável pela API. Nenhum método aqui executa SQL recebido do cliente.
"""


class AdminModel:
    def __init__(self, database):
        self._database = database

    def resetar(self):
        conn = self._database.connection()
        with conn:  # transação única
            conn.execute("DELETE FROM itens_pedido")
            conn.execute("DELETE FROM pedidos")
            conn.execute("DELETE FROM produtos")
            conn.execute("DELETE FROM usuarios")
