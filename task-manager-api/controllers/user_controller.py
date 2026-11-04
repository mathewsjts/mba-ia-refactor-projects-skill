from flask import g, jsonify, request

from controllers.validators import parse_pagination, validate_login, validate_user_create, validate_user_update
from routes.serializers import (
    serialize_task_summary,
    serialize_user,
    serialize_user_detail,
    serialize_user_with_task_count,
)


class UserController:
    def __init__(self, user_service, auth_service):
        self._users = user_service
        self._auth = auth_service

    def list(self):
        limit, offset = parse_pagination(request.args)
        users = self._users.list(g.user, limit, offset)
        return jsonify([serialize_user_with_task_count(user, count) for user, count in users]), 200

    def show(self, user_id):
        user, tasks = self._users.get_detail(g.user, user_id)
        return jsonify(serialize_user_detail(user, tasks)), 200

    def tasks(self, user_id):
        return jsonify([serialize_task_summary(task) for task in self._users.list_tasks(user_id)]), 200

    def create(self):
        fields = validate_user_create(request.get_json(silent=True))
        return jsonify(serialize_user(self._users.register(g.get('user'), fields))), 201

    def update(self, user_id):
        user = self._users.get_own_or_admin(g.user, user_id)
        fields = validate_user_update(request.get_json(silent=True))
        return jsonify(serialize_user(self._users.update(g.user, user, fields))), 200

    def delete(self, user_id):
        self._users.delete(g.user, user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def login(self):
        email, password = validate_login(request.get_json(silent=True))
        user, token = self._auth.login(email, password)
        return jsonify({'message': 'Login realizado com sucesso', 'user': serialize_user(user), 'token': token}), 200
