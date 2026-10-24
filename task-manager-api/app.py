"""Composition root: cria e conecta as dependências e expõe o entry point (T11)."""
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
from models.repositories import CategoryRepository, TaskRepository, UserRepository
from routes.report_routes import create_report_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService


def create_app(settings=None):
    settings = settings or Settings.from_env()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    # repositórios → serviços → controllers
    task_repo = TaskRepository()
    user_repo = UserRepository()
    category_repo = CategoryRepository()
    auth_service = AuthService(settings.secret_key, settings.auth_token_max_age)

    task_service = TaskService(task_repo, user_repo, category_repo)
    user_service = UserService(user_repo, task_repo, auth_service)
    category_service = CategoryService(category_repo)
    report_service = ReportService(task_repo, user_repo, category_repo)

    task_controller = TaskController(task_service)
    user_controller = UserController(user_service)
    category_controller = CategoryController(category_service)
    report_controller = ReportController(report_service, user_service)

    app.register_blueprint(create_task_blueprint(task_controller, auth_service))
    app.register_blueprint(create_user_blueprint(user_controller, auth_service))
    app.register_blueprint(create_report_blueprint(report_controller, category_controller, auth_service))

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


settings = Settings.from_env()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
