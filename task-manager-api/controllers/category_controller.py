from flask import jsonify, request

from controllers.validators import parse_pagination, validate_category_create, validate_category_update
from routes.serializers import serialize_category, serialize_category_listing


class CategoryController:
    def __init__(self, category_service):
        self._service = category_service

    def index(self):
        limit, offset = parse_pagination(request.args)
        rows = self._service.list_categories(limit, offset)
        return jsonify([serialize_category_listing(category, count) for category, count in rows]), 200

    def create(self):
        fields = validate_category_create(request.get_json())
        return jsonify(serialize_category(self._service.create(fields))), 201

    def update(self, cat_id):
        category = self._service.get(cat_id)
        fields = validate_category_update(request.get_json())
        return jsonify(serialize_category(self._service.update(category, fields))), 200

    def delete(self, cat_id):
        self._service.delete(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
