from sqlalchemy import func, select

from database import db, fits_db_integer, transaction
from models.clock import utcnow
from models.task import Task


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default='#000000')
    created_at = db.Column(db.DateTime, default=utcnow)

    # Sem cascade de delete: ao apagar a categoria o ORM anula tasks.category_id e as tasks ficam (T15).
    tasks = db.relationship('Task', back_populates='category')


class CategoryRepository:
    def get(self, category_id):
        if not fits_db_integer(category_id):
            return None
        return db.session.get(Category, category_id)

    def list_with_task_count(self, limit=None, offset=0):
        stmt = (
            select(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).all()

    def count(self):
        return db.session.scalar(select(func.count(Category.id)))

    def add(self, category):
        with transaction() as session:
            session.add(category)
        return category

    def update(self, category, fields):
        with transaction():
            for name, value in fields.items():
                setattr(category, name, value)
        return category

    def delete(self, category):
        with transaction() as session:
            session.delete(category)
