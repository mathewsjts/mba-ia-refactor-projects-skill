from sqlalchemy import func, select

from clock import utcnow
from constants import DEFAULT_COLOR
from database import commit, db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    # -- acesso a dados -------------------------------------------------
    @staticmethod
    def get(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def list_all(limit=None, offset=0):
        stmt = select(Category).order_by(Category.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def count():
        return db.session.scalar(select(func.count()).select_from(Category))

    @staticmethod
    def task_counts():
        from models.task import Task

        rows = db.session.execute(
            select(Task.category_id, func.count(Task.id)).group_by(Task.category_id)
        ).all()
        return {category_id: total for category_id, total in rows}

    def save(self, error_message):
        db.session.add(self)
        commit(error_message)

    def delete(self, error_message):
        """Remove a categoria. As tasks têm seu category_id anulado pelo ORM."""
        db.session.delete(self)
        commit(error_message)
