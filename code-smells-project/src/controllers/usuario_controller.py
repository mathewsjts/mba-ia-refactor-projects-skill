from flask import g, jsonify, request

from src.controllers.validators import validar_login, validar_paginacao, validar_usuario
from src.views.serializers import serialize_login, serialize_usuario, serialize_usuarios


class UsuarioController:
    def __init__(self, usuario_service, auth_service):
        self._service = usuario_service
        self._auth = auth_service

    def listar(self):
        limit, offset = validar_paginacao(request.args)
        usuarios = self._service.listar(limit, offset)
        return jsonify({"dados": serialize_usuarios(usuarios), "sucesso": True}), 200

    def mostrar(self, usuario_id):
        self._auth.garantir_dono_ou_admin(g.usuario, usuario_id)
        usuario = self._service.obter(usuario_id)
        return jsonify({"dados": serialize_usuario(usuario), "sucesso": True}), 200

    def criar(self):
        nome, email, senha = validar_usuario(request.get_json(silent=True))
        usuario_id = self._service.criar(nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        email, senha = validar_login(request.get_json(silent=True))
        usuario = self._service.autenticar(email, senha)
        token = self._auth.emitir_token(usuario)
        return jsonify({
            "dados": serialize_login(usuario, token),
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200
