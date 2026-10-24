"""Acesso a dados por domínio, com API moderna do SQLAlchemy 2.0 (T08, T12)."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User


class TaskRepository:
    def get(self, task_id):
        return db.session.get(Task, task_id)

    def list_all(self):
        return db.session.execute(select(Task).order_by(Task.id)).scalars().all()

    def list_with_relations(self):
        stmt = select(Task).options(
            joinedload(Task.user), joinedload(Task.category)
        ).order_by(Task.id)
        return db.session.execute(stmt).scalars().all()

    def list_by_user(self, user_id):
        stmt = select(Task).filter_by(user_id=user_id).order_by(Task.id)
        return db.session.execute(stmt).scalars().all()

    def search(self, query=None, status=None, priority=None, user_id=None):
        stmt = select(Task)
        if query:
            stmt = stmt.where(or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == int(priority))
        if user_id:
            stmt = stmt.where(Task.user_id == int(user_id))
        return db.session.execute(stmt.order_by(Task.id)).scalars().all()

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)


class UserRepository:
    def get(self, user_id):
        return db.session.get(User, user_id)

    def get_by_email(self, email):
        return db.session.execute(select(User).filter_by(email=email)).scalars().first()

    def list_all(self):
        return db.session.execute(select(User).order_by(User.id)).scalars().all()

    def count(self):
        return db.session.scalar(select(func.count()).select_from(User))

    def task_counts(self):
        rows = db.session.execute(
            select(Task.user_id, func.count(Task.id)).group_by(Task.user_id)
        ).all()
        return {uid: total for uid, total in rows if uid is not None}

    def add(self, user):
        db.session.add(user)

    def delete(self, user):
        db.session.delete(user)


class CategoryRepository:
    def get(self, category_id):
        return db.session.get(Category, category_id)

    def list_all(self):
        return db.session.execute(select(Category).order_by(Category.id)).scalars().all()

    def count(self):
        return db.session.scalar(select(func.count()).select_from(Category))

    def task_counts(self):
        rows = db.session.execute(
            select(Task.category_id, func.count(Task.id)).group_by(Task.category_id)
        ).all()
        return {cid: total for cid, total in rows if cid is not None}

    def add(self, category):
        db.session.add(category)

    def delete(self, category):
        db.session.delete(category)
