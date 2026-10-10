"""Controller das operações administrativas (rotas protegidas por token — T14)."""
import logging

from flask import jsonify, request

from src.errors import ValidationError

logger = logging.getLogger(__name__)


class AdminController:
    def __init__(self, admin_model):
        self._admin = admin_model

    def resetar(self):
        self._admin.resetar()
        logger.warning("Banco de dados resetado")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        dados = request.get_json(silent=True) or {}
        query = dados.get("sql", "")
        if not query:
            raise ValidationError("Query não informada")
        is_select, linhas = self._admin.executar_query(query)
        if is_select:
            return jsonify({"dados": linhas, "sucesso": True}), 200
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
