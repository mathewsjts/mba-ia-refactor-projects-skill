"""Regras de negócio de tarefas (T04)."""
from datetime import datetime

from database import db
from errors import NotFoundError, ValidationError
from models.task import Task
from constants import MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, TASK_STATUSES


def _join_tags(tags):
    return ','.join(tags) if isinstance(tags, list) else tags


def _parse_due_date(value, message):
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except (ValueError, TypeError):
        raise ValidationError(message)


class TaskService:
    def __init__(self, task_repository, user_repository, category_repository):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository

    def list_tasks(self):
        return self._tasks.list_with_relations()

    def search_tasks(self, query=None, status=None, priority=None, user_id=None):
        return self._tasks.search(query=query, status=status, priority=priority, user_id=user_id)

    def get_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def create_task(self, validated):
        self._ensure_related_exist(validated.get('user_id'), validated.get('category_id'))
        task = Task()
        task.title = validated['title']
        task.description = validated['description']
        task.status = validated['status']
        task.priority = validated['priority']
        task.user_id = validated['user_id']
        task.category_id = validated['category_id']
        if validated['due_date']:
            task.due_date = _parse_due_date(validated['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
        if validated['tags']:
            task.tags = _join_tags(validated['tags'])
        self._tasks.add(task)
        db.session.commit()
        return task

    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            if len(data['title']) < MIN_TITLE_LENGTH:
                raise ValidationError('Título muito curto')
            if len(data['title']) > MAX_TITLE_LENGTH:
                raise ValidationError('Título muito longo')
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            if data['status'] not in TASK_STATUSES:
                raise ValidationError('Status inválido')
            task.status = data['status']
        if 'priority' in data:
            if data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
                raise ValidationError('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']
        if 'user_id' in data:
            if data['user_id'] and self._users.get(data['user_id']) is None:
                raise NotFoundError('Usuário não encontrado')
            task.user_id = data['user_id']
        if 'category_id' in data:
            if data['category_id'] and self._categories.get(data['category_id']) is None:
                raise NotFoundError('Categoria não encontrada')
            task.category_id = data['category_id']
        if 'due_date' in data:
            task.due_date = _parse_due_date(data['due_date'], 'Formato de data inválido') if data['due_date'] else None
        if 'tags' in data:
            task.tags = _join_tags(data['tags'])

        db.session.commit()
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        self._tasks.delete(task)
        db.session.commit()

    def stats(self):
        tasks = self._tasks.list_all()
        total = len(tasks)
        by_status = {status: 0 for status in TASK_STATUSES}
        overdue = 0
        for task in tasks:
            if task.status in by_status:
                by_status[task.status] += 1
            if task.is_overdue():
                overdue += 1
        done = by_status['done']
        return {
            'total': total,
            'pending': by_status['pending'],
            'in_progress': by_status['in_progress'],
            'done': done,
            'cancelled': by_status['cancelled'],
            'overdue': overdue,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }

    def _ensure_related_exist(self, user_id, category_id):
        if user_id and self._users.get(user_id) is None:
            raise NotFoundError('Usuário não encontrado')
        if category_id and self._categories.get(category_id) is None:
            raise NotFoundError('Categoria não encontrada')
