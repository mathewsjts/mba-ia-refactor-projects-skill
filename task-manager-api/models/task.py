from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from clock import utcnow
from constants import CLOSED_STATUSES
from database import commit, db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    # -- acesso a dados -------------------------------------------------
    @staticmethod
    def get(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def list_all(limit=None, offset=0):
        stmt = select(Task).order_by(Task.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def list_with_relations(limit=None, offset=0):
        stmt = (
            select(Task)
            .options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def list_for_user(user_id):
        return db.session.execute(
            select(Task).filter_by(user_id=user_id).order_by(Task.id)
        ).scalars().all()

    @staticmethod
    def search(q=None, status=None, priority=None, user_id=None, limit=None, offset=0):
        stmt = select(Task)
        if q:
            stmt = stmt.where(or_(Task.title.like(f"%{q}%"), Task.description.like(f"%{q}%")))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == int(priority))
        if user_id:
            stmt = stmt.where(Task.user_id == int(user_id))
        stmt = stmt.order_by(Task.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def list_overdue(now):
        return db.session.execute(
            select(Task)
            .where(
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status.notin_(list(CLOSED_STATUSES)),
            )
            .order_by(Task.id)
        ).scalars().all()

    @staticmethod
    def count():
        return db.session.scalar(select(func.count()).select_from(Task))

    @staticmethod
    def count_overdue(now):
        return db.session.scalar(
            select(func.count())
            .select_from(Task)
            .where(
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status.notin_(list(CLOSED_STATUSES)),
            )
        )

    @staticmethod
    def count_by_status():
        rows = db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
        return {status: total for status, total in rows}

    @staticmethod
    def count_by_priority():
        rows = db.session.execute(
            select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        ).all()
        return {priority: total for priority, total in rows}

    @staticmethod
    def count_by_user():
        rows = db.session.execute(
            select(Task.user_id, func.count(Task.id)).group_by(Task.user_id)
        ).all()
        return {user_id: total for user_id, total in rows}

    @staticmethod
    def done_count_by_user():
        rows = db.session.execute(
            select(Task.user_id, func.count(Task.id))
            .where(Task.status == "done")
            .group_by(Task.user_id)
        ).all()
        return {user_id: total for user_id, total in rows}

    @staticmethod
    def count_created_since(since):
        return db.session.scalar(
            select(func.count()).select_from(Task).where(Task.created_at >= since)
        )

    @staticmethod
    def count_done_since(since):
        return db.session.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.status == "done", Task.updated_at >= since)
        )

    def save(self, error_message):
        db.session.add(self)
        commit(error_message)

    def delete(self, error_message):
        db.session.delete(self)
        commit(error_message)
