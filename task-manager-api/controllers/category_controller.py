from flask import jsonify, request

from routes.serializers import serialize_category, serialize_category_summary


class CategoryController:
    def __init__(self, category_service):
        self._service = category_service

    def index(self):
        categories = self._service.list_categories()
        return jsonify([serialize_category_summary(cat, count) for cat, count in categories]), 200

    def create(self):
        category = self._service.create_category(request.get_json(silent=True))
        return jsonify(serialize_category(category)), 201

    def update(self, cat_id):
        category = self._service.update_category(cat_id, request.get_json(silent=True))
        return jsonify(serialize_category(category)), 200

    def delete(self, cat_id):
        self._service.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
