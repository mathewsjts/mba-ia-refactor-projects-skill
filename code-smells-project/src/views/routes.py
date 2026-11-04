from flask import Blueprint

from src.middlewares.auth import require_auth


def create_routes(controllers, auth_service):
    produtos = controllers["produto"]
    usuarios = controllers["usuario"]
    pedidos = controllers["pedido"]
    relatorios = controllers["relatorio"]
    meta = controllers["meta"]

    autenticado = require_auth(auth_service)
    admin = require_auth(auth_service, somente_admin=True)

    bp = Blueprint("api", __name__)
    rota = bp.add_url_rule

    rota("/produtos", "listar_produtos", produtos.listar, methods=["GET"])
    rota("/produtos/busca", "buscar_produtos", produtos.buscar, methods=["GET"])
    rota("/produtos/<int:produto_id>", "buscar_produto", produtos.mostrar, methods=["GET"])
    rota("/produtos", "criar_produto", admin(produtos.criar), methods=["POST"])
    rota("/produtos/<int:produto_id>", "atualizar_produto", admin(produtos.atualizar), methods=["PUT"])
    rota("/produtos/<int:produto_id>", "deletar_produto", admin(produtos.remover), methods=["DELETE"])

    rota("/usuarios", "listar_usuarios", admin(usuarios.listar), methods=["GET"])
    rota("/usuarios/<int:usuario_id>", "buscar_usuario", autenticado(usuarios.mostrar), methods=["GET"])
    rota("/usuarios", "criar_usuario", usuarios.criar, methods=["POST"])
    rota("/login", "login", usuarios.login, methods=["POST"])

    rota("/pedidos", "criar_pedido", autenticado(pedidos.criar), methods=["POST"])
    rota("/pedidos", "listar_todos_pedidos", admin(pedidos.listar), methods=["GET"])
    rota(
        "/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
        autenticado(pedidos.listar_por_usuario), methods=["GET"],
    )
    rota(
        "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
        admin(pedidos.atualizar_status), methods=["PUT"],
    )

    rota("/relatorios/vendas", "relatorio_vendas", admin(relatorios.vendas), methods=["GET"])

    rota("/health", "health_check", meta.health, methods=["GET"])
    rota("/", "index", meta.index, methods=["GET"])
    return bp
