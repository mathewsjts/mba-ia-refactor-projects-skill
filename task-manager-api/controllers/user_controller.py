from flask import g, jsonify, request

from controllers.validators import (
    parse_pagination,
    require_object,
    validate_login,
    validate_user_create,
    validate_user_update,
)
from routes.serializers import serialize_user, serialize_user_detail, serialize_user_listing, serialize_user_task


class UserController:
    def __init__(self, user_service, auth_service):
        self._service = user_service
        self._auth = auth_service

    def index(self):
        limit, offset = parse_pagination(request.args)
        rows = self._service.list_users(limit, offset)
        return jsonify([serialize_user_listing(user, task_count) for user, task_count in rows]), 200

    def show(self, user_id):
        user, tasks = self._service.get_with_tasks(user_id)
        return jsonify(serialize_user_detail(user, tasks)), 200

    def create(self):
        fields = validate_user_create(request.get_json(), self._service.ensure_email_available)
        user = self._service.create(fields, actor=g.current_user)
        return jsonify(serialize_user(user)), 201

    def update(self, user_id):
        actor = g.current_user
        user = self._service.get(user_id)
        data = require_object(request.get_json())
        self._service.authorize_update(actor, user, data.keys())
        fields = validate_user_update(
            data, lambda email: self._service.ensure_email_available(email, exclude_id=user.id)
        )
        return jsonify(serialize_user(self._service.update(user, fields))), 200

    def delete(self, user_id):
        self._service.delete(g.current_user, user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def tasks(self, user_id):
        tasks = self._service.get_user_tasks(user_id)
        return jsonify([serialize_user_task(task) for task in tasks]), 200

    def login(self):
        email, password = validate_login(request.get_json())
        user, token = self._auth.login(email, password)
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': serialize_user(user),
            'token': token,
        }), 200
