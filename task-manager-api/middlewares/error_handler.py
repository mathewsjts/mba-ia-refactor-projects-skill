"""Tratamento de erro centralizado (T10 / AP-15)."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # 404 de rota inexistente, 405 etc. mantêm o comportamento nativo.
        return err

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({"error": "Erro interno"}), 500
