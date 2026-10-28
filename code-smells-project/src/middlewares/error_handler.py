"""Tratamento de erros centralizado (T10).

Traduz erros de domínio para o formato de erro que o projeto já usa; erros
inesperados viram 500 genérico, sem vazar `str(e)`.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify(err.to_body()), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # 404 de rota inexistente (inclui /admin/* removidas), 405 etc. seguem nativos.
        return err

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
