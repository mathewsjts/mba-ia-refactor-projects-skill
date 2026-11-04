from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from constants import CLOSED_TASK_STATUSES, DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, HIGH_PRIORITY_MAX, MAX_DB_INTEGER
from database import commit, db, paginate
from models.clock import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    # Remover o usuário remove as tasks dele; remover a categoria só desvincula as tasks.
    user = db.relationship('User', backref=db.backref('tasks', cascade='all'))
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_TASK_STATUSES


def _overdue(now):
    return (
        Task.due_date.isnot(None)
        & (Task.due_date < now)
        & or_(Task.status.is_(None), Task.status.notin_(CLOSED_TASK_STATUSES))
    )


def _count(*conditions):
    return db.session.scalar(select(func.count(Task.id)).where(*conditions))


class TaskRepository:
    def get(self, task_id):
        if not 0 < task_id <= MAX_DB_INTEGER:
            return None
        return db.session.get(Task, task_id)

    def list_with_relations(self, limit=None, offset=0):
        query = select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        return paginate(query, limit, offset)

    def search(self, text=None, status=None, priority=None, user_id=None, limit=None, offset=0):
        query = select(Task)
        if text:
            query = query.where(or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%')))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return paginate(query.order_by(Task.id), limit, offset)

    def list_by_user(self, user_id):
        return db.session.execute(select(Task).where(Task.user_id == user_id).order_by(Task.id)).scalars().all()

    def list_overdue(self, now):
        return db.session.execute(select(Task).where(_overdue(now)).order_by(Task.id)).scalars().all()

    def count(self, user_id=None):
        return _count(Task.user_id == user_id) if user_id is not None else _count()

    def count_overdue(self, now, user_id=None):
        conditions = [_overdue(now)]
        if user_id is not None:
            conditions.append(Task.user_id == user_id)
        return _count(*conditions)

    def count_high_priority(self, user_id):
        return _count(Task.user_id == user_id, Task.priority <= HIGH_PRIORITY_MAX)

    def count_created_since(self, since):
        return _count(Task.created_at >= since)

    def count_done_since(self, since):
        return _count(Task.status == 'done', Task.updated_at >= since)

    def count_by_status(self, user_id=None):
        query = select(Task.status, func.count(Task.id)).group_by(Task.status)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return dict(db.session.execute(query).all())

    def count_by_priority(self):
        return dict(db.session.execute(select(Task.priority, func.count(Task.id)).group_by(Task.priority)).all())

    def count_by_category(self):
        query = select(Task.category_id, func.count(Task.id)).group_by(Task.category_id)
        return dict(db.session.execute(query).all())

    def count_by_user(self):
        return dict(db.session.execute(select(Task.user_id, func.count(Task.id)).group_by(Task.user_id)).all())

    def count_done_by_user(self):
        query = select(Task.user_id, func.count(Task.id)).where(Task.status == 'done').group_by(Task.user_id)
        return dict(db.session.execute(query).all())

    def add(self, task):
        db.session.add(task)
        commit()

    def save(self):
        commit()

    def delete(self, task):
        db.session.delete(task)
        commit()
