import logging

from clock import utcnow
from controllers.validators import (
    normalize_tags,
    parse_due_date,
    require_payload,
    validate_priority,
    validate_status,
    validate_title,
)
from constants import DEFAULT_PRIORITY
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


class TaskService:
    def list(self, limit=None, offset=0):
        return Task.list_with_relations(limit=limit, offset=offset)

    def get(self, task_id):
        task = Task.get(task_id)
        if not task:
            raise NotFoundError("Task não encontrada")
        return task

    def search(self, q="", status="", priority="", user_id="", limit=None, offset=0):
        return Task.search(
            q=q or None,
            status=status or None,
            priority=priority or None,
            user_id=user_id or None,
            limit=limit,
            offset=offset,
        )

    def stats(self):
        now = utcnow()
        by_status = Task.count_by_status()
        total = Task.count()
        done = by_status.get("done", 0)
        return {
            "total": total,
            "pending": by_status.get("pending", 0),
            "in_progress": by_status.get("in_progress", 0),
            "done": done,
            "cancelled": by_status.get("cancelled", 0),
            "overdue": Task.count_overdue(now),
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        }

    def create(self, data):
        require_payload(data)
        title = validate_title(data.get("title"), required=True)
        description = data.get("description", "")
        status = data.get("status", "pending")
        validate_status(status)
        priority = data.get("priority", DEFAULT_PRIORITY)
        validate_priority(priority)
        user_id = data.get("user_id")
        category_id = data.get("category_id")

        if user_id and not User.get(user_id):
            raise NotFoundError("Usuário não encontrado")
        if category_id and not Category.get(category_id):
            raise NotFoundError("Categoria não encontrada")

        due_date = data.get("due_date")
        tags = data.get("tags")

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id
        if due_date:
            task.due_date = parse_due_date(due_date, "Formato de data inválido. Use YYYY-MM-DD")
        if tags:
            task.tags = normalize_tags(tags)

        task.save("Erro ao criar task")
        logger.info("Task criada: %s - %s", task.id, task.title)
        return task

    def update(self, task_id, data):
        task = Task.get(task_id)
        if not task:
            raise NotFoundError("Task não encontrada")
        require_payload(data)

        if "title" in data:
            task.title = validate_title(data["title"], required=False)
        if "description" in data:
            task.description = data["description"]
        if "status" in data:
            validate_status(data["status"])
            task.status = data["status"]
        if "priority" in data:
            validate_priority(data["priority"])
            task.priority = data["priority"]
        if "user_id" in data:
            if data["user_id"] and not User.get(data["user_id"]):
                raise NotFoundError("Usuário não encontrado")
            task.user_id = data["user_id"]
        if "category_id" in data:
            if data["category_id"] and not Category.get(data["category_id"]):
                raise NotFoundError("Categoria não encontrada")
            task.category_id = data["category_id"]
        if "due_date" in data:
            if data["due_date"]:
                task.due_date = parse_due_date(data["due_date"], "Formato de data inválido")
            else:
                task.due_date = None
        if "tags" in data:
            task.tags = normalize_tags(data["tags"])

        task.updated_at = utcnow()
        task.save("Erro ao atualizar")
        logger.info("Task atualizada: %s", task.id)
        return task

    def delete(self, task_id):
        task = self.get(task_id)
        task.delete("Erro ao deletar")
        logger.info("Task deletada: %s", task_id)
