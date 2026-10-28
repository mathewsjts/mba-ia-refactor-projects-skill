"""Controller de usuários e login."""
from flask import jsonify, request

from src.controllers.validators import parse_paginacao, validar_login, validar_usuario
from src.views.serializers import serialize_login, serialize_usuario, serialize_usuarios


class UsuarioController:
    def __init__(self, usuario_service):
        self._service = usuario_service

    def listar(self):
        limit, offset = parse_paginacao(request.args)
        usuarios = self._service.listar(limit, offset)
        return jsonify({"dados": serialize_usuarios(usuarios), "sucesso": True}), 200

    def buscar(self, usuario_id):
        usuario = self._service.buscar(usuario_id)
        return jsonify({"dados": serialize_usuario(usuario), "sucesso": True}), 200

    def criar(self):
        nome, email, senha = validar_usuario(request.get_json(silent=True))
        novo_id = self._service.criar(nome, email, senha)
        return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201

    def login(self):
        email, senha = validar_login(request.get_json(silent=True))
        usuario = self._service.login(email, senha)
        return jsonify({"dados": serialize_login(usuario), "sucesso": True, "mensagem": "Login OK"}), 200
