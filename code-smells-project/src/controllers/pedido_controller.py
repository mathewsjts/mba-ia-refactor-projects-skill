"""Controller de pedidos."""
from flask import jsonify, request

from src.controllers.validators import validar_pedido, validar_status
from src.views.serializers import serialize_pedidos


class PedidoController:
    def __init__(self, pedido_service):
        self._service = pedido_service

    def criar(self):
        usuario_id, itens = validar_pedido(request.get_json(silent=True))
        resultado = self._service.criar(usuario_id, itens)
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_todos(self):
        pedidos = self._service.listar()
        return jsonify({"dados": serialize_pedidos(pedidos), "sucesso": True}), 200

    def listar_usuario(self, usuario_id):
        pedidos = self._service.listar(usuario_id=usuario_id)
        return jsonify({"dados": serialize_pedidos(pedidos), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        novo_status = validar_status(request.get_json(silent=True))
        self._service.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
