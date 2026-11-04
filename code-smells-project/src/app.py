import logging

import click
from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.meta_controller import MetaController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.database import Database
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.auth_service import AuthService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.saude_service import SaudeService
from src.services.usuario_service import UsuarioService
from src.views.routes import create_routes


def create_app(settings=None):
    """Composition root: único ponto que conhece as implementações concretas."""
    settings = settings or Settings.from_env()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app, origins=settings.cors_origins)

    database = Database(settings.database_path)
    app.teardown_appcontext(database.close)
    with app.app_context():
        database.inicializar(com_usuarios_exemplo=not settings.production)

    produto_model = ProdutoModel(database)
    usuario_model = UsuarioModel(database)
    pedido_model = PedidoModel(database)
    admin_model = AdminModel(database)

    auth_service = AuthService(settings.secret_key, settings.token_max_age, usuario_model)
    usuario_service = UsuarioService(usuario_model)
    pedido_service = PedidoService(pedido_model, produto_model, usuario_service, NotificacaoService())

    controllers = {
        "produto": ProdutoController(ProdutoService(produto_model)),
        "usuario": UsuarioController(usuario_service, auth_service),
        "pedido": PedidoController(pedido_service, auth_service),
        "relatorio": RelatorioController(RelatorioService(pedido_model)),
        "meta": MetaController(SaudeService(produto_model, usuario_model, pedido_model), settings.env),
    }
    app.register_blueprint(create_routes(controllers, auth_service))
    register_error_handlers(app)

    @app.cli.command("reset-db")
    def reset_db():
        """Apaga todos os dados (uso local; substitui a antiga rota POST /admin/reset-db)."""
        admin_model.resetar()
        click.echo("Banco de dados resetado")

    return app
