"""Agregações de relatórios, calculadas numa única varredura (T04, T08)."""
from datetime import timedelta

from clock import utcnow
from constants import CLOSED_STATUSES


class ReportService:
    def __init__(self, task_repository, user_repository, category_repository):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository

    def summary(self):
        now = utcnow()
        seven_days_ago = now - timedelta(days=7)
        tasks = self._tasks.list_all()
        users = self._users.list_all()

        status_counts = {'pending': 0, 'in_progress': 0, 'done': 0, 'cancelled': 0}
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        overdue_list = []
        recent_created = 0
        recent_done = 0
        tasks_by_user = {}

        for task in tasks:
            if task.status in status_counts:
                status_counts[task.status] += 1
            if task.priority in priority_counts:
                priority_counts[task.priority] += 1
            if task.is_overdue(now):
                overdue_list.append({
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                })
            if task.created_at and task.created_at >= seven_days_ago:
                recent_created += 1
            if task.status == 'done' and task.updated_at and task.updated_at >= seven_days_ago:
                recent_done += 1
            tasks_by_user.setdefault(task.user_id, []).append(task)

        user_stats = []
        for user in users:
            user_tasks = tasks_by_user.get(user.id, [])
            total = len(user_tasks)
            completed = sum(1 for t in user_tasks if t.status == 'done')
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': len(tasks),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {
                'pending': status_counts['pending'],
                'in_progress': status_counts['in_progress'],
                'done': status_counts['done'],
                'cancelled': status_counts['cancelled'],
            },
            'tasks_by_priority': {
                'critical': priority_counts[1],
                'high': priority_counts[2],
                'medium': priority_counts[3],
                'low': priority_counts[4],
                'minimal': priority_counts[5],
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_created,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user):
        now = utcnow()
        tasks = self._tasks.list_by_user(user.id)
        total = len(tasks)
        done = pending = in_progress = cancelled = overdue = high_priority = 0
        for task in tasks:
            if task.status == 'done':
                done += 1
            elif task.status == 'pending':
                pending += 1
            elif task.status == 'in_progress':
                in_progress += 1
            elif task.status == 'cancelled':
                cancelled += 1
            if task.priority <= 2:
                high_priority += 1
            if task.due_date and task.due_date < now and task.status not in CLOSED_STATUSES:
                overdue += 1

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            },
        }
