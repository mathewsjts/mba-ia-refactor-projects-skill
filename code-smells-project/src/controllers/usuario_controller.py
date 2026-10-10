"""Controller de usuários e login."""
import logging

from flask import jsonify, request

from src.controllers.validators import validar_login, validar_usuario
from src.views.serializers import serialize_usuario, serialize_usuarios

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuario_service):
        self._service = usuario_service

    def listar(self):
        usuarios = self._service.listar()
        return jsonify({"dados": serialize_usuarios(usuarios), "sucesso": True}), 200

    def buscar(self, id):
        usuario = self._service.buscar(id)
        return jsonify({"dados": serialize_usuario(usuario), "sucesso": True}), 200

    def criar(self):
        campos = validar_usuario(request.get_json(silent=True))
        usuario_id = self._service.criar(campos["nome"], campos["email"], campos["senha"])
        logger.info("Usuário criado: %s", campos["email"])
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        email, senha = validar_login(request.get_json(silent=True))
        usuario = self._service.autenticar(email, senha)
        logger.info("Login bem-sucedido: %s", email)
        return jsonify({
            "dados": usuario,
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200
