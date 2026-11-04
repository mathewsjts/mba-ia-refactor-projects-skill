import logging

import click
from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.system_controller import SystemController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from controllers.validators import validate_user_create
from database import db, init_database
from errors import AppError
from middlewares.auth import optional_auth, require_auth
from middlewares.error_handler import register_error_handlers
from models import CategoryRepository, TaskRepository, UserRepository
from routes.category_routes import register_category_routes
from routes.report_routes import register_report_routes
from routes.system_routes import register_system_routes
from routes.task_routes import register_task_routes
from routes.user_routes import register_user_routes
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or Settings.from_env()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    if settings.secret_key_is_ephemeral:
        logger.warning('SECRET_KEY não definida: usando uma chave aleatória deste processo (tokens não sobrevivem ao restart)')

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
    )
    CORS(app, origins=list(settings.cors_origins))
    init_database(app)

    tasks = TaskRepository()
    users = UserRepository()
    categories = CategoryRepository()

    auth_service = AuthService(users, settings.secret_key, settings.token_max_age)
    task_service = TaskService(tasks, users, categories)
    user_service = UserService(users, tasks)
    category_service = CategoryService(categories, tasks)
    report_service = ReportService(tasks, users, categories)

    auth = require_auth(auth_service)
    register_system_routes(app, SystemController())
    register_task_routes(app, TaskController(task_service), auth)
    register_user_routes(app, UserController(user_service, auth_service), auth, optional_auth(auth_service))
    register_category_routes(app, CategoryController(category_service), auth)
    register_report_routes(app, ReportController(report_service), auth)
    register_error_handlers(app)
    _register_commands(app, user_service)
    return app


def _register_commands(app, user_service):
    @app.cli.command('create-admin')
    @click.option('--name', prompt=True)
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(name, email, password):
        """Cria um admin (o cadastro público só cria contas com perfil `user`)."""
        try:
            fields = validate_user_create({'name': name, 'email': email, 'password': password})
            user = user_service.create_admin(fields)
        except AppError as err:
            raise click.ClickException(err.message)
        click.echo(f'Admin criado: {user.email} (id {user.id})')


settings = Settings.from_env()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
