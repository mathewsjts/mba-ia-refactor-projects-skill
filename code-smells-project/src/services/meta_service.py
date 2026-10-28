"""Metadados de saúde da aplicação para o /health (T13 / BC-03).

Não expõe segredo, flag de debug nem caminho do banco — só status, conexão,
contagens e versão.
"""
from src.config.settings import APP_VERSION


class MetaService:
    def __init__(self, database, produto_model, usuario_model, pedido_model):
        self._database = database
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model

    def health(self):
        self._database.ping()
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": APP_VERSION,
        }
