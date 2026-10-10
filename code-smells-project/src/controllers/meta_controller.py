"""Controller de rotas meta: índice da API e health check.

O health não expõe mais secret_key/debug/db_path/ambiente (BC-01); mantém
status, database, counts e versao.
"""
from flask import jsonify

VERSAO = "1.0.0"


class MetaController:
    def __init__(self, produto_model, usuario_model, pedido_model):
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": VERSAO,
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
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": VERSAO,
        }), 200
