from flask import jsonify, request

from controllers.validators import pagination_args
from routes.serializers import (
    serialize_task,
    serialize_task_detail,
    serialize_task_enriched,
)


class TaskController:
    def __init__(self, service):
        self._service = service

    def index(self):
        limit, offset = pagination_args(request.args)
        tasks = self._service.list(limit=limit, offset=offset)
        return jsonify([serialize_task_enriched(t) for t in tasks]), 200

    def show(self, task_id):
        task = self._service.get(task_id)
        return jsonify(serialize_task_detail(task)), 200

    def create(self):
        task = self._service.create(request.get_json())
        return jsonify(serialize_task(task)), 201

    def update(self, task_id):
        task = self._service.update(task_id, request.get_json())
        return jsonify(serialize_task(task)), 200

    def delete(self, task_id):
        self._service.delete(task_id)
        return jsonify({"message": "Task deletada com sucesso"}), 200

    def search(self):
        limit, offset = pagination_args(request.args)
        tasks = self._service.search(
            q=request.args.get("q", ""),
            status=request.args.get("status", ""),
            priority=request.args.get("priority", ""),
            user_id=request.args.get("user_id", ""),
            limit=limit,
            offset=offset,
        )
        return jsonify([serialize_task(t) for t in tasks]), 200

    def stats(self):
        return jsonify(self._service.stats()), 200
