"""Mapeamento de rotas → controllers (camada View).

Preserva exatamente método, path e parâmetros do contrato original. As rotas
administrativas passam pelo middleware require_admin (T14, BC-03).
"""
from flask import Blueprint

from src.middlewares.admin_auth import require_admin


def create_routes(produto, usuario, pedido, relatorio, admin, meta):
    bp = Blueprint("api", __name__)

    # Meta
    bp.add_url_rule("/", "index", meta.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", meta.health, methods=["GET"])

    # Produtos
    bp.add_url_rule("/produtos", "listar_produtos", produto.listar, methods=["GET"])
    bp.add_url_rule("/produtos/busca", "buscar_produtos", produto.buscar_produtos, methods=["GET"])
    bp.add_url_rule("/produtos/<int:id>", "buscar_produto", produto.buscar, methods=["GET"])
    bp.add_url_rule("/produtos", "criar_produto", produto.criar, methods=["POST"])
    bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto.atualizar, methods=["PUT"])
    bp.add_url_rule("/produtos/<int:id>", "deletar_produto", produto.deletar, methods=["DELETE"])

    # Usuários
    bp.add_url_rule("/usuarios", "listar_usuarios", usuario.listar, methods=["GET"])
    bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario.buscar, methods=["GET"])
    bp.add_url_rule("/usuarios", "criar_usuario", usuario.criar, methods=["POST"])
    bp.add_url_rule("/login", "login", usuario.login, methods=["POST"])

    # Pedidos
    bp.add_url_rule("/pedidos", "criar_pedido", pedido.criar, methods=["POST"])
    bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido.listar_todos, methods=["GET"])
    bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                    pedido.listar_usuario, methods=["GET"])
    bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                    pedido.atualizar_status, methods=["PUT"])

    # Relatórios
    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio.vendas, methods=["GET"])

    # Administrativas (protegidas por X-Admin-Token)
    bp.add_url_rule("/admin/reset-db", "reset_database",
                    require_admin(admin.resetar), methods=["POST"])
    bp.add_url_rule("/admin/query", "executar_query",
                    require_admin(admin.executar_query), methods=["POST"])

    return bp
