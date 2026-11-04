from constants import CATEGORY_NOT_FOUND_MESSAGE
from errors import NotFoundError
from models.category import Category


class CategoryService:
    def __init__(self, category_repository):
        self._categories = category_repository

    def list_categories(self, limit=None, offset=0):
        return self._categories.list_with_task_count(limit, offset)

    def get(self, category_id):
        category = self._categories.get(category_id)
        if category is None:
            raise NotFoundError(CATEGORY_NOT_FOUND_MESSAGE)
        return category

    def create(self, fields):
        return self._categories.add(Category(**fields))

    def update(self, category, fields):
        return self._categories.update(category, fields)

    def delete(self, category_id):
        self._categories.delete(self.get(category_id))
