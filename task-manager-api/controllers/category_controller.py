from flask import jsonify, request

from controllers.validators import pagination_args
from routes.serializers import serialize_category, serialize_category_list


class CategoryController:
    def __init__(self, service):
        self._service = service

    def index(self):
        limit, offset = pagination_args(request.args)
        categories = self._service.list(limit=limit, offset=offset)
        counts = self._service.task_counts()
        return jsonify([serialize_category_list(c, counts.get(c.id, 0)) for c in categories]), 200

    def create(self):
        category = self._service.create(request.get_json())
        return jsonify(serialize_category(category)), 201

    def update(self, category_id):
        category = self._service.update(category_id, request.get_json())
        return jsonify(serialize_category(category)), 200

    def delete(self, category_id):
        self._service.delete(category_id)
        return jsonify({"message": "Categoria deletada"}), 200
