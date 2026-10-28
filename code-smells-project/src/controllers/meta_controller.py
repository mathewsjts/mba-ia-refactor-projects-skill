"""Controller de metadados: index e health."""
from flask import jsonify

from src.config.settings import APP_VERSION


class MetaController:
    def __init__(self, meta_service):
        self._service = meta_service

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        return jsonify(self._service.health()), 200
