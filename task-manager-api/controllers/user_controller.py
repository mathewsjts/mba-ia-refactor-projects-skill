from flask import jsonify, request

from controllers.validators import validate_user_create
from routes.serializers import (
    serialize_user,
    serialize_user_detail,
    serialize_user_summary,
    serialize_user_task,
)


class UserController:
    def __init__(self, user_service):
        self._service = user_service

    def index(self):
        users = self._service.list_users()
        return jsonify([serialize_user_summary(user, count) for user, count in users]), 200

    def show(self, user_id):
        user, tasks = self._service.get_user_with_tasks(user_id)
        return jsonify(serialize_user_detail(user, tasks)), 200

    def create(self):
        validated = validate_user_create(request.get_json(silent=True))
        user = self._service.create_user(validated)
        return jsonify(serialize_user(user)), 201

    def update(self, user_id):
        user = self._service.update_user(user_id, request.get_json(silent=True))
        return jsonify(serialize_user(user)), 200

    def delete(self, user_id):
        self._service.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def user_tasks(self, user_id):
        _, tasks = self._service.get_user_with_tasks(user_id)
        return jsonify([serialize_user_task(t) for t in tasks]), 200

    def login(self):
        user, token = self._service.login(request.get_json(silent=True))
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': serialize_user(user),
            'token': token,
        }), 200
