from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from constants import CLOSED_TASK_STATUSES, DONE_STATUS
from database import db, fits_db_integer, transaction
from models.clock import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    # Remoção do usuário apaga as tasks dele; remoção da categoria anula o vínculo (T15).
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_TASK_STATUSES

    @staticmethod
    def overdue_clause(now):
        """Mesma regra de `is_overdue`, em SQL (status nulo conta como aberto, como em Python)."""
        return (
            Task.due_date.isnot(None)
            & (Task.due_date < now)
            & or_(Task.status.is_(None), Task.status.notin_(CLOSED_TASK_STATUSES))
        )


def _paginate(stmt, limit, offset):
    if limit is None:
        return stmt
    return stmt.limit(limit).offset(offset)


class TaskRepository:
    def get(self, task_id):
        if not fits_db_integer(task_id):
            return None
        return db.session.get(Task, task_id)

    def list(self, limit=None, offset=0, with_relations=False):
        stmt = select(Task).order_by(Task.id)
        if with_relations:
            # Usuário e categoria vêm no mesmo SELECT, sem uma consulta por task (T08).
            stmt = stmt.options(joinedload(Task.user), joinedload(Task.category))
        return db.session.execute(_paginate(stmt, limit, offset)).scalars().all()

    def search(self, text=None, status=None, priority=None, user_id=None, limit=None, offset=0):
        stmt = select(Task)
        if text:
            stmt = stmt.where(or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%')))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        stmt = _paginate(stmt.order_by(Task.id), limit, offset)
        return db.session.execute(stmt).scalars().all()

    def list_by_user(self, user_id):
        stmt = select(Task).where(Task.user_id == user_id).order_by(Task.id)
        return db.session.execute(stmt).scalars().all()

    def list_overdue(self, now):
        stmt = select(Task).where(Task.overdue_clause(now)).order_by(Task.id)
        return db.session.execute(stmt).scalars().all()

    def count(self):
        return db.session.scalar(select(func.count(Task.id)))

    def count_by_status(self):
        return dict(db.session.execute(select(Task.status, func.count(Task.id)).group_by(Task.status)).all())

    def count_by_priority(self):
        return dict(db.session.execute(select(Task.priority, func.count(Task.id)).group_by(Task.priority)).all())

    def count_overdue(self, now):
        return db.session.scalar(select(func.count(Task.id)).where(Task.overdue_clause(now)))

    def count_created_since(self, since):
        return db.session.scalar(select(func.count(Task.id)).where(Task.created_at >= since))

    def count_done_since(self, since):
        stmt = select(func.count(Task.id)).where(Task.status == DONE_STATUS, Task.updated_at >= since)
        return db.session.scalar(stmt)

    def add(self, task):
        with transaction() as session:
            session.add(task)
        return task

    def update(self, task, fields):
        with transaction():
            for name, value in fields.items():
                setattr(task, name, value)
        return task

    def delete(self, task):
        with transaction() as session:
            session.delete(task)
