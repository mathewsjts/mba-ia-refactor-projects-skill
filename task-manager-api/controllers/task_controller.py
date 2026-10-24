from flask import jsonify, request

from controllers.validators import validate_task_create
from routes.serializers import serialize_task, serialize_task_listed, serialize_task_with_overdue


class TaskController:
    def __init__(self, task_service):
        self._service = task_service

    def index(self):
        tasks = self._service.list_tasks()
        return jsonify([serialize_task_listed(t) for t in tasks]), 200

    def show(self, task_id):
        task = self._service.get_task(task_id)
        return jsonify(serialize_task_with_overdue(task)), 200

    def create(self):
        validated = validate_task_create(request.get_json(silent=True))
        task = self._service.create_task(validated)
        return jsonify(serialize_task(task)), 201

    def update(self, task_id):
        task = self._service.update_task(task_id, request.get_json(silent=True))
        return jsonify(serialize_task(task)), 200

    def delete(self, task_id):
        self._service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search(self):
        tasks = self._service.search_tasks(
            query=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=request.args.get('priority', ''),
            user_id=request.args.get('user_id', ''),
        )
        return jsonify([serialize_task(t) for t in tasks]), 200

    def stats(self):
        return jsonify(self._service.stats()), 200
