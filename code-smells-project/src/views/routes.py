"""Mapeamento de rotas → controllers (View). Sem regra de negócio nem SQL.

As rotas /admin/query e /admin/reset-db foram removidas (BC-01/BC-02, T14):
execução de SQL do cliente e destruição em massa não pertencem à API.
"""
from flask import Blueprint


def create_routes(controllers):
    produto = controllers["produto"]
    usuario = controllers["usuario"]
    pedido = controllers["pedido"]
    relatorio = controllers["relatorio"]
    meta = controllers["meta"]

    bp = Blueprint("api", __name__)

    bp.add_url_rule("/produtos", "listar_produtos", produto.listar, methods=["GET"])
    bp.add_url_rule("/produtos/busca", "buscar_produtos", produto.buscar_catalogo, methods=["GET"])
    bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produto.buscar, methods=["GET"])
    bp.add_url_rule("/produtos", "criar_produto", produto.criar, methods=["POST"])
    bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produto.atualizar, methods=["PUT"])
    bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produto.deletar, methods=["DELETE"])

    bp.add_url_rule("/usuarios", "listar_usuarios", usuario.listar, methods=["GET"])
    bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuario.buscar, methods=["GET"])
    bp.add_url_rule("/usuarios", "criar_usuario", usuario.criar, methods=["POST"])
    bp.add_url_rule("/login", "login", usuario.login, methods=["POST"])

    bp.add_url_rule("/pedidos", "criar_pedido", pedido.criar, methods=["POST"])
    bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido.listar_todos, methods=["GET"])
    bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido.listar_por_usuario, methods=["GET"])
    bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido.atualizar_status, methods=["PUT"])

    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio.vendas, methods=["GET"])

    bp.add_url_rule("/health", "health_check", meta.health, methods=["GET"])
    bp.add_url_rule("/", "index", meta.index, methods=["GET"])

    return bp
