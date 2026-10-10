from sqlalchemy import func, select

from clock import utcnow
from database import commit, db
from passwords import hash_password, verify_password


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, plain):
        self.password = hash_password(plain)

    def check_password(self, plain):
        return verify_password(self.password, plain)

    def is_admin(self):
        return self.role == "admin"

    # -- acesso a dados -------------------------------------------------
    @staticmethod
    def get(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        return db.session.execute(
            select(User).filter_by(email=email)
        ).scalars().first()

    @staticmethod
    def list_all(limit=None, offset=0):
        stmt = select(User).order_by(User.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def count():
        return db.session.scalar(select(func.count()).select_from(User))

    def save(self, error_message):
        db.session.add(self)
        commit(error_message)

    def delete_with_tasks(self, error_message):
        """Remove as tasks do usuário e o próprio usuário numa transação (T07/T15)."""
        for task in list(self.tasks):
            db.session.delete(task)
        db.session.delete(self)
        commit(error_message)
