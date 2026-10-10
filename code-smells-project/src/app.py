"""Composition root: cria as dependências concretas, injeta-as e registra rotas e
middlewares (T11). É o único lugar que conhece as implementações concretas.
"""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.admin_controller import AdminController
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
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.views.routes import create_routes


def create_app(settings=None):
    settings = settings or Settings.from_env()
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["ADMIN_TOKEN"] = settings.admin_token
    CORS(app, origins=settings.cors_origins)

    database = Database(settings.database_path)
    app.teardown_appcontext(database.close)

    # Models (dados)
    produto_model = ProdutoModel(database)
    usuario_model = UsuarioModel(database)
    pedido_model = PedidoModel(database)
    admin_model = AdminModel(database)

    # Cria o schema e o seed uma vez no boot (o original fazia na primeira conexão).
    with app.app_context():
        database.setup()

    # Services (regra de negócio)
    notificador = NotificacaoService()
    produto_service = ProdutoService(produto_model)
    usuario_service = UsuarioService(usuario_model)
    pedido_service = PedidoService(pedido_model, produto_model, notificador)
    relatorio_service = RelatorioService(pedido_model)

    # Controllers (fluxo HTTP)
    controllers = (
        ProdutoController(produto_service),
        UsuarioController(usuario_service),
        PedidoController(pedido_service),
        RelatorioController(relatorio_service),
        AdminController(admin_model),
        MetaController(produto_model, usuario_model, pedido_model),
    )
    app.register_blueprint(create_routes(*controllers))
    register_error_handlers(app)
    return app
