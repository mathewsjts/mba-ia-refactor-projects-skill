from flask import jsonify

VERSAO_API = "1.0.0"

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class MetaController:
    def __init__(self, saude_service, ambiente):
        self._saude = saude_service
        self._ambiente = ambiente

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": VERSAO_API,
            "endpoints": ENDPOINTS,
        })

    def health(self):
        contagens = self._saude.contagens()
        if contagens is None:
            return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": VERSAO_API,
            "ambiente": self._ambiente,
        }), 200
