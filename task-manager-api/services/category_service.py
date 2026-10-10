from constants import DEFAULT_COLOR
from controllers.validators import require_payload
from errors import NotFoundError, ValidationError
from models.category import Category


class CategoryService:
    def list(self, limit=None, offset=0):
        return Category.list_all(limit=limit, offset=offset)

    def task_counts(self):
        return Category.task_counts()

    def get(self, category_id):
        category = Category.get(category_id)
        if not category:
            raise NotFoundError("Categoria não encontrada")
        return category

    def create(self, data):
        require_payload(data)
        name = data.get("name")
        if not name:
            raise ValidationError("Nome é obrigatório")

        category = Category()
        category.name = name
        category.description = data.get("description", "")
        category.color = data.get("color", DEFAULT_COLOR)
        category.save("Erro ao criar categoria")
        return category

    def update(self, category_id, data):
        category = self.get(category_id)
        if "name" in data:
            category.name = data["name"]
        if "description" in data:
            category.description = data["description"]
        if "color" in data:
            category.color = data["color"]
        category.save("Erro ao atualizar")
        return category

    def delete(self, category_id):
        category = self.get(category_id)
        category.delete("Erro ao deletar")
