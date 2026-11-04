import logging

from errors import NotFoundError, ValidationError
from models.clock import parse_date, utcnow
from models.task import Task
from services.authorization import ensure_owner_or_admin
from services.stats import completion_rate

logger = logging.getLogger(__name__)

UPDATABLE_FIELDS = ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'tags')


def _parse_due_date(value, message):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError(message)
    return parsed


class TaskService:
    def __init__(self, task_repository, user_repository, category_repository):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository

    def list(self, limit=None, offset=0):
        return self._tasks.list_with_relations(limit, offset)

    def search(self, filters, limit=None, offset=0):
        return self._tasks.search(limit=limit, offset=offset, **filters)

    def get(self, task_id):
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task

    def stats(self, now=None):
        now = now or utcnow()
        by_status = self._tasks.count_by_status()
        total = self._tasks.count()
        done = by_status.get('done', 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': self._tasks.count_overdue(now),
            'completion_rate': completion_rate(done, total),
        }

    def create(self, actor, fields):
        fields = dict(fields)
        fields.setdefault('user_id', actor.id)            # sem dono no corpo: quem chama é o dono
        ensure_owner_or_admin(actor, fields['user_id'])   # criar para outra conta: só admin
        self._ensure_references(fields)
        task = Task(**{name: fields[name] for name in UPDATABLE_FIELDS if name in fields})
        task.due_date = _parse_due_date(fields.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD')
        self._tasks.add(task)
        logger.info('Task criada: %s', task.id)
        return task

    def get_writable(self, actor, task_id):
        task = self.get(task_id)                          # 404 antes do 403
        ensure_owner_or_admin(actor, task.user_id)
        return task

    def update(self, actor, task, fields):
        if 'user_id' in fields:
            ensure_owner_or_admin(actor, fields['user_id'])  # transferir para outra conta: só admin
        self._ensure_references(fields)
        due_date = _parse_due_date(fields['due_date'], 'Formato de data inválido') if 'due_date' in fields else None

        for name in UPDATABLE_FIELDS:
            if name in fields:
                setattr(task, name, fields[name])
        if 'due_date' in fields:
            task.due_date = due_date
        task.updated_at = utcnow()
        self._tasks.save()
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete(self, actor, task_id):
        task = self.get_writable(actor, task_id)
        self._tasks.delete(task)
        logger.info('Task deletada: %s', task_id)

    def _ensure_references(self, fields):
        if fields.get('user_id') and self._users.get(fields['user_id']) is None:
            raise NotFoundError('Usuário não encontrado')
        if fields.get('category_id') and self._categories.get(fields['category_id']) is None:
            raise NotFoundError('Categoria não encontrada')
