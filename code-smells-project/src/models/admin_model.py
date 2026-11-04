class AdminModel:
    """Operações de manutenção usadas só pelo comando de linha `flask --app app reset-db`."""

    def __init__(self, database):
        self._database = database

    def resetar(self):
        with self._database.transacao() as conn:
            # Filhas antes das mães, para não violar as chaves estrangeiras.
            conn.execute("DELETE FROM itens_pedido")
            conn.execute("DELETE FROM pedidos")
            conn.execute("DELETE FROM produtos")
            conn.execute("DELETE FROM usuarios")
