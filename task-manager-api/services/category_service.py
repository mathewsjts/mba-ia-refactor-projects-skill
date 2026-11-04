from constants import DEFAULT_CATEGORY_COLOR
from errors import NotFoundError
from models.category import Category
from services.authorization import ensure_admin

UPDATABLE_FIELDS = ('name', 'description', 'color')


class CategoryService:
    """Categorias são compartilhadas (sem dono): só admin escreve."""

    def __init__(self, category_repository, task_repository):
        self._categories = category_repository
        self._tasks = task_repository

    def list(self, limit=None, offset=0):
        categories = self._categories.list(limit, offset)
        task_counts = self._tasks.count_by_category()
        return [(category, task_counts.get(category.id, 0)) for category in categories]

    def get(self, category_id):
        category = self._categories.get(category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category

    def authorize_write(self, actor):
        ensure_admin(actor)

    def create(self, actor, fields):
        ensure_admin(actor)
        category = Category(
            name=fields['name'],
            description=fields.get('description', ''),
            color=fields.get('color', DEFAULT_CATEGORY_COLOR),
        )
        self._categories.add(category)
        return category

    def get_writable(self, actor, category_id):
        category = self.get(category_id)                  # 404 antes do 403
        ensure_admin(actor)
        return category

    def update(self, category, fields):
        for name in UPDATABLE_FIELDS:
            if name in fields:
                setattr(category, name, fields[name])
        self._categories.save()
        return category

    def delete(self, actor, category_id):
        category = self.get_writable(actor, category_id)
        self._categories.delete(category)                 # as tasks ficam sem categoria (ORM + ON DELETE SET NULL)
