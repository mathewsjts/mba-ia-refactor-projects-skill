import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        corpo = {"erro": err.mensagem}
        if err.incluir_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return err  # 404 de rota inexistente, 405 etc. seguem com o comportamento nativo

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
