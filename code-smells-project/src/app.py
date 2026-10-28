"""Composition root: cria as dependências concretas, injeta e registra tudo (T11)."""
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
from src.services.meta_service import MetaService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.views.routes import create_routes


def create_app(settings=None):
    settings = settings or Settings.from_env()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app, origins=settings.cors_origins)

    # Infraestrutura
    database = Database(settings.database_path)
    database.initialize()  # schema + seed uma vez no boot (como o original)
    app.teardown_appcontext(database.close)

    # Models
    produto_model = ProdutoModel(database)
    usuario_model = UsuarioModel(database)
    pedido_model = PedidoModel(database)
    admin_model = AdminModel(database)

    # Services
    notificacao_service = NotificacaoService()
    produto_service = ProdutoService(produto_model)
    usuario_service = UsuarioService(usuario_model)
    pedido_service = PedidoService(pedido_model, produto_model, notificacao_service)
    relatorio_service = RelatorioService(pedido_model)
    meta_service = MetaService(database, produto_model, usuario_model, pedido_model)

    # Controllers
    controllers = {
        "produto": ProdutoController(produto_service),
        "usuario": UsuarioController(usuario_service),
        "pedido": PedidoController(pedido_service),
        "relatorio": RelatorioController(relatorio_service),
        "meta": MetaController(meta_service),
    }

    app.register_blueprint(create_routes(controllers))
    register_error_handlers(app)

    @app.cli.command("reset-db")
    def reset_db():
        """Apaga todos os dados (uso local — substitui a antiga rota /admin/reset-db)."""
        admin_model.resetar()
        click.echo("Banco de dados resetado")

    return app
