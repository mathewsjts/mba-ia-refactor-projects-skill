from sqlalchemy import func, select

from constants import DEFAULT_CATEGORY_COLOR, MAX_DB_INTEGER
from database import commit, db, paginate
from models.clock import utcnow


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_CATEGORY_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)


class CategoryRepository:
    def get(self, category_id):
        if not 0 < category_id <= MAX_DB_INTEGER:
            return None
        return db.session.get(Category, category_id)

    def list(self, limit=None, offset=0):
        return paginate(select(Category).order_by(Category.id), limit, offset)

    def count(self):
        return db.session.scalar(select(func.count(Category.id)))

    def add(self, category):
        db.session.add(category)
        commit()

    def save(self):
        commit()

    def delete(self, category):
        db.session.delete(category)
        commit()
