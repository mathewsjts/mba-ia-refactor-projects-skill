"""Composition root: cria as dependências, conecta as camadas e expõe o app.

Mantém `app` e `db` no nível do módulo porque `seed.py` faz `from app import app, db`.
"""
import datetime

from flask import Flask
from flask_cors import CORS

from config import Settings
from database import db
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from middlewares.error_handler import register_error_handlers
from routes.category_routes import create_category_routes
from routes.report_routes import create_report_routes
from routes.task_routes import create_task_routes
from routes.user_routes import create_user_routes
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService

# Garante que as entidades sejam registradas no metadata antes de create_all.
import models  # noqa: F401


def _register_misc_routes(app):
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    def health():
        return {"status": "ok", "timestamp": str(datetime.datetime.now())}

    app.add_url_rule("/", "index", index)
    app.add_url_rule("/health", "health", health)


def create_app(settings=None):
    settings = settings or Settings.from_env()

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["ADMIN_TOKEN"] = settings.admin_token

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    auth_service = AuthService(settings.secret_key)
    app.register_blueprint(create_task_routes(TaskController(TaskService())))
    app.register_blueprint(create_user_routes(UserController(UserService(), auth_service)))
    app.register_blueprint(create_category_routes(CategoryController(CategoryService())))
    app.register_blueprint(create_report_routes(ReportController(ReportService())))
    _register_misc_routes(app)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


settings = Settings.from_env()
app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
