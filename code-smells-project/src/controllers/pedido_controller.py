from flask import g, jsonify, request

from src.controllers.validators import validar_paginacao, validar_pedido, validar_status
from src.views.serializers import serialize_pedidos


class PedidoController:
    def __init__(self, pedido_service, auth_service):
        self._service = pedido_service
        self._auth = auth_service

    def criar(self):
        usuario_id, itens = validar_pedido(request.get_json(silent=True))
        self._auth.garantir_dono_ou_admin(g.usuario, usuario_id)
        resultado = self._service.criar(usuario_id, itens)
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar(self):
        limit, offset = validar_paginacao(request.args)
        pedidos = self._service.listar(limit, offset)
        return jsonify({"dados": serialize_pedidos(pedidos), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        self._auth.garantir_dono_ou_admin(g.usuario, usuario_id)
        pedidos = self._service.listar_por_usuario(usuario_id)
        return jsonify({"dados": serialize_pedidos(pedidos), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        status = validar_status(request.get_json(silent=True))
        self._service.atualizar_status(pedido_id, status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
