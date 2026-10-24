"""Regras de negócio de categorias (T04)."""
from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from constants import DEFAULT_COLOR


class CategoryService:
    def __init__(self, category_repository):
        self._categories = category_repository

    def list_categories(self):
        categories = self._categories.list_all()
        counts = self._categories.task_counts()
        return [(category, counts.get(category.id, 0)) for category in categories]

    def get_category(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')
        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_COLOR)
        self._categories.add(category)
        db.session.commit()
        return category

    def update_category(self, category_id, data):
        category = self.get_category(category_id)
        data = data or {}
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']
        db.session.commit()
        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        self._categories.delete(category)
        db.session.commit()
