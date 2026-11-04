"""Composition root: único lugar que cria as dependências concretas e as conecta (T11)."""
import logging

import click
from flask import Flask
from flask_cors import CORS

from config import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from controllers.validators import validate_user_create
from database import db, init_database
from errors import AppError
from middlewares.error_handler import register_error_handlers
from models.category import CategoryRepository
from models.task import TaskRepository
from models.user import UserRepository
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService

__all__ = ['app', 'create_app', 'db']


def create_app(settings=None):
    settings = settings or Settings.from_env()
    logging.basicConfig(level=settings.log_level)

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    CORS(app, origins=settings.cors_origins)
    init_database(app)

    task_repository = TaskRepository()
    user_repository = UserRepository()
    category_repository = CategoryRepository()

    auth_service = AuthService(user_repository, settings.secret_key, settings.token_max_age)
    task_service = TaskService(task_repository, user_repository, category_repository)
    user_service = UserService(user_repository, task_repository)
    category_service = CategoryService(category_repository)
    report_service = ReportService(task_repository, user_repository, category_repository, user_service)

    app.register_blueprint(create_system_blueprint())
    app.register_blueprint(create_task_blueprint(TaskController(task_service), auth_service))
    app.register_blueprint(create_user_blueprint(UserController(user_service, auth_service), auth_service))
    app.register_blueprint(create_category_blueprint(CategoryController(category_service), auth_service))
    app.register_blueprint(create_report_blueprint(ReportController(report_service), auth_service))
    register_error_handlers(app)

    @app.cli.command('create-admin')
    @click.option('--name', prompt=True)
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(name, email, password):
        """Cria a conta de administrador (primeiro admin em produção, sem seed)."""
        try:
            fields = validate_user_create(
                {'name': name, 'email': email, 'password': password}, user_service.ensure_email_available
            )
            user = user_service.create_admin(fields)
        except AppError as err:
            raise click.ClickException(err.message)
        click.echo(f'Admin criado: {user.id} - {user.email}')

    return app


settings = Settings.from_env()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
