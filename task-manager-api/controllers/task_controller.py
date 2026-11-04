from flask import g, jsonify, request

from controllers.validators import parse_pagination, parse_search_args, validate_task_create, validate_task_update
from routes.serializers import serialize_task, serialize_task_detail, serialize_task_with_relations


class TaskController:
    def __init__(self, task_service):
        self._service = task_service

    def list(self):
        limit, offset = parse_pagination(request.args)
        return jsonify([serialize_task_with_relations(task) for task in self._service.list(limit, offset)]), 200

    def show(self, task_id):
        return jsonify(serialize_task_detail(self._service.get(task_id))), 200

    def search(self):
        filters = parse_search_args(request.args)
        limit, offset = parse_pagination(request.args)
        return jsonify([serialize_task(task) for task in self._service.search(filters, limit, offset)]), 200

    def stats(self):
        return jsonify(self._service.stats()), 200

    def create(self):
        fields = validate_task_create(request.get_json(silent=True))
        return jsonify(serialize_task(self._service.create(g.user, fields))), 201

    def update(self, task_id):
        task = self._service.get_writable(g.user, task_id)
        fields = validate_task_update(request.get_json(silent=True))
        return jsonify(serialize_task(self._service.update(g.user, task, fields))), 200

    def delete(self, task_id):
        self._service.delete(g.user, task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
