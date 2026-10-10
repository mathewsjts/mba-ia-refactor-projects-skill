from flask import jsonify, request

from controllers.validators import pagination_args
from routes.serializers import (
    serialize_task_summary,
    serialize_user,
    serialize_user_detail,
    serialize_user_list,
)


class UserController:
    def __init__(self, service, auth_service):
        self._service = service
        self._auth = auth_service

    def index(self):
        limit, offset = pagination_args(request.args)
        users = self._service.list(limit=limit, offset=offset)
        counts = self._service.task_counts()
        return jsonify([serialize_user_list(u, counts.get(u.id, 0)) for u in users]), 200

    def show(self, user_id):
        user = self._service.get(user_id)
        tasks = self._service.tasks_for(user_id)
        return jsonify(serialize_user_detail(user, tasks)), 200

    def create(self):
        user = self._service.create(request.get_json())
        return jsonify(serialize_user(user)), 201

    def update(self, user_id):
        user = self._service.update(user_id, request.get_json())
        return jsonify(serialize_user(user)), 200

    def delete(self, user_id):
        self._service.delete(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    def tasks(self, user_id):
        self._service.get(user_id)
        tasks = self._service.tasks_for(user_id)
        return jsonify([serialize_task_summary(t) for t in tasks]), 200

    def login(self):
        user = self._service.authenticate(request.get_json())
        return (
            jsonify(
                {
                    "message": "Login realizado com sucesso",
                    "user": serialize_user(user),
                    "token": self._auth.issue_token(user),
                }
            ),
            200,
        )
