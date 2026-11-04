from datetime import timedelta

from constants import PRIORITY_LABELS, RECENT_ACTIVITY_DAYS
from errors import NotFoundError
from models.clock import utcnow
from services.authorization import ensure_owner_or_admin
from services.stats import completion_rate


class ReportService:
    def __init__(self, task_repository, user_repository, category_repository):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository

    def summary(self, now=None):
        now = now or utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        overdue = self._tasks.list_overdue(now)
        totals = self._tasks.count_by_user()
        completed = self._tasks.count_done_by_user()

        productivity = []
        for user in self._users.list():
            total = totals.get(user.id, 0)
            done = completed.get(user.id, 0)
            productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': done,
                'completion_rate': completion_rate(done, total),
            })

        return {
            'generated_at': now,
            'overview': {
                'total_tasks': self._tasks.count(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in ('pending', 'in_progress', 'done', 'cancelled')},
            'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
            'overdue': [(task, (now - task.due_date).days) for task in overdue],
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(since),
                'tasks_completed_last_7_days': self._tasks.count_done_since(since),
            },
            'user_productivity': productivity,
        }

    def user_report(self, actor, user_id, now=None):
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')  # 404 antes do 403
        ensure_owner_or_admin(actor, user.id)
        now = now or utcnow()
        by_status = self._tasks.count_by_status(user.id)
        total = self._tasks.count(user.id)
        done = by_status.get('done', 0)
        return user, {
            'total_tasks': total,
            'done': done,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'cancelled': by_status.get('cancelled', 0),
            'overdue': self._tasks.count_overdue(now, user.id),
            'high_priority': self._tasks.count_high_priority(user.id),
            'completion_rate': completion_rate(done, total),
        }
