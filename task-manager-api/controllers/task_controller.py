from flask import jsonify, request

from controllers.validators import parse_pagination, parse_task_search, validate_task_create, validate_task_update
from routes.serializers import serialize_task, serialize_task_detail, serialize_task_listing


class TaskController:
    def __init__(self, task_service):
        self._service = task_service

    def index(self):
        limit, offset = parse_pagination(request.args)
        tasks = self._service.list_tasks(limit, offset)
        return jsonify([serialize_task_listing(task) for task in tasks]), 200

    def show(self, task_id):
        return jsonify(serialize_task_detail(self._service.get(task_id))), 200

    def create(self):
        fields = validate_task_create(
            request.get_json(), self._service.ensure_user_exists, self._service.ensure_category_exists
        )
        return jsonify(serialize_task(self._service.create(fields))), 201

    def update(self, task_id):
        task = self._service.get(task_id)
        fields = validate_task_update(
            request.get_json(), self._service.ensure_user_exists, self._service.ensure_category_exists
        )
        return jsonify(serialize_task(self._service.update(task, fields))), 200

    def delete(self, task_id):
        self._service.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search(self):
        filters = parse_task_search(request.args)
        limit, offset = parse_pagination(request.args)
        tasks = self._service.search(filters, limit, offset)
        return jsonify([serialize_task(task) for task in tasks]), 200

    def stats(self):
        return jsonify(self._service.stats()), 200
