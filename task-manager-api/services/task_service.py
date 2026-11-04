import logging

from constants import (
    CATEGORY_NOT_FOUND_MESSAGE,
    DONE_STATUS,
    TASK_NOT_FOUND_MESSAGE,
    TASK_STATUSES,
    USER_NOT_FOUND_MESSAGE,
)
from errors import NotFoundError
from models.clock import utcnow
from models.task import Task

logger = logging.getLogger(__name__)


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


class TaskService:
    def __init__(self, task_repository, user_repository, category_repository):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository

    def list_tasks(self, limit=None, offset=0):
        return self._tasks.list(limit, offset, with_relations=True)

    def search(self, filters, limit=None, offset=0):
        return self._tasks.search(limit=limit, offset=offset, **filters)

    def get(self, task_id):
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFoundError(TASK_NOT_FOUND_MESSAGE)
        return task

    def ensure_user_exists(self, user_id):
        if self._users.get(user_id) is None:
            raise NotFoundError(USER_NOT_FOUND_MESSAGE)

    def ensure_category_exists(self, category_id):
        if self._categories.get(category_id) is None:
            raise NotFoundError(CATEGORY_NOT_FOUND_MESSAGE)

    def create(self, fields):
        task = self._tasks.add(Task(**fields))
        logger.info("Task criada: %s - %s", task.id, task.title)
        return task

    def update(self, task, fields):
        # O original marcava updated_at em toda atualização, mesmo sem mudança de valor.
        task = self._tasks.update(task, {**fields, "updated_at": utcnow()})
        logger.info("Task atualizada: %s", task.id)
        return task

    def delete(self, task_id):
        self._tasks.delete(self.get(task_id))
        logger.info("Task deletada: %s", task_id)

    def stats(self):
        by_status = self._tasks.count_by_status()
        total = self._tasks.count()
        stats = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        stats.update({
            "total": total,
            "overdue": self._tasks.count_overdue(utcnow()),
            "completion_rate": completion_rate(by_status.get(DONE_STATUS, 0), total),
        })
        return stats
