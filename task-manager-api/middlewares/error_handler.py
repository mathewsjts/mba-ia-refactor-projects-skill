import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return err  # 404 de rota inexistente, 405 etc. seguem com o comportamento nativo

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        db.session.rollback()
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
