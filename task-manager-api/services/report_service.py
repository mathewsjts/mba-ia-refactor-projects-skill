from datetime import timedelta

from constants import DONE_STATUS, HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from models.clock import utcnow
from services.task_service import completion_rate


class ReportService:
    def __init__(self, task_repository, user_repository, category_repository, user_service):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository
        self._user_service = user_service

    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        overdue = self._tasks.list_overdue(now)

        return {
            'generated_at': str(utcnow()),
            'overview': {
                'total_tasks': self._tasks.count(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(since),
                'tasks_completed_last_7_days': self._tasks.count_done_since(since),
            },
            'user_productivity': [
                {
                    'user_id': user_id,
                    'user_name': name,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'completion_rate': completion_rate(completed, total),
                }
                for user_id, name, total, completed in self._users.productivity()
            ],
        }

    def user_report(self, user_id):
        user, tasks = self._user_service.get_with_tasks(user_id)
        now = utcnow()
        counts = {status: 0 for status in TASK_STATUSES}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        total = len(tasks)

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                **counts,
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': completion_rate(counts[DONE_STATUS], total),
            },
        }
