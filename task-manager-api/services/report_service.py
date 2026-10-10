from datetime import timedelta

from clock import utcnow
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User

HIGH_PRIORITY_THRESHOLD = 2


class ReportService:
    def summary(self):
        now = utcnow()
        by_status = Task.count_by_status()
        by_priority = Task.count_by_priority()

        overdue_tasks = Task.list_overdue(now)
        overdue_list = [
            {
                "id": task.id,
                "title": task.title,
                "due_date": str(task.due_date),
                "days_overdue": (now - task.due_date).days,
            }
            for task in overdue_tasks
        ]

        seven_days_ago = now - timedelta(days=7)
        recent_tasks = Task.count_created_since(seven_days_ago)
        recent_done = Task.count_done_since(seven_days_ago)

        totals = Task.count_by_user()
        done_totals = Task.done_count_by_user()
        user_stats = []
        for user in User.list_all():
            total = totals.get(user.id, 0)
            completed = done_totals.get(user.id, 0)
            user_stats.append(
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0,
                }
            )

        return {
            "generated_at": str(now),
            "overview": {
                "total_tasks": Task.count(),
                "total_users": User.count(),
                "total_categories": Category.count(),
            },
            "tasks_by_status": {
                "pending": by_status.get("pending", 0),
                "in_progress": by_status.get("in_progress", 0),
                "done": by_status.get("done", 0),
                "cancelled": by_status.get("cancelled", 0),
            },
            "tasks_by_priority": {
                "critical": by_priority.get(1, 0),
                "high": by_priority.get(2, 0),
                "medium": by_priority.get(3, 0),
                "low": by_priority.get(4, 0),
                "minimal": by_priority.get(5, 0),
            },
            "overdue": {
                "count": len(overdue_list),
                "tasks": overdue_list,
            },
            "recent_activity": {
                "tasks_created_last_7_days": recent_tasks,
                "tasks_completed_last_7_days": recent_done,
            },
            "user_productivity": user_stats,
        }

    def user_report(self, user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        now = utcnow()
        tasks = Task.list_for_user(user_id)
        total = len(tasks)
        done = pending = in_progress = cancelled = overdue = high_priority = 0

        for task in tasks:
            if task.status == "done":
                done += 1
            elif task.status == "pending":
                pending += 1
            elif task.status == "in_progress":
                in_progress += 1
            elif task.status == "cancelled":
                cancelled += 1

            if task.priority <= HIGH_PRIORITY_THRESHOLD:
                high_priority += 1
            if task.is_overdue(now):
                overdue += 1

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
            "statistics": {
                "total_tasks": total,
                "done": done,
                "pending": pending,
                "in_progress": in_progress,
                "cancelled": cancelled,
                "overdue": overdue,
                "high_priority": high_priority,
                "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
            },
        }
