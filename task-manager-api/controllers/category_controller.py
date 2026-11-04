from flask import g, jsonify, request

from controllers.validators import parse_pagination, validate_category_create, validate_category_update
from routes.serializers import serialize_category, serialize_category_with_task_count


class CategoryController:
    def __init__(self, category_service):
        self._service = category_service

    def list(self):
        limit, offset = parse_pagination(request.args)
        categories = self._service.list(limit, offset)
        return jsonify([serialize_category_with_task_count(category, count) for category, count in categories]), 200

    def create(self):
        self._service.authorize_write(g.user)              # 403 antes do 400
        fields = validate_category_create(request.get_json(silent=True))
        return jsonify(serialize_category(self._service.create(g.user, fields))), 201

    def update(self, category_id):
        category = self._service.get_writable(g.user, category_id)
        fields = validate_category_update(request.get_json(silent=True))
        return jsonify(serialize_category(self._service.update(category, fields))), 200

    def delete(self, category_id):
        self._service.delete(g.user, category_id)
        return jsonify({'message': 'Categoria deletada'}), 200
