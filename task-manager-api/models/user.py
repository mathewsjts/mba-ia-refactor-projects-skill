from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError

from constants import ADMIN_ROLE, DONE_STATUS, EMAIL_TAKEN_MESSAGE
from database import db, fits_db_integer, transaction
from errors import ConflictError
from models.clock import utcnow
from models.passwords import hash_password, verify_password
from models.task import Task


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Apagar o usuário apaga as tasks dele na mesma transação (T15).
    tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, plain):
        self.password = hash_password(plain)

    def check_password(self, plain):
        ok, needs_rehash = verify_password(self.password, plain)
        if ok and needs_rehash:
            self.password = hash_password(plain)
        return ok

    def is_admin(self):
        return self.role == ADMIN_ROLE


def _is_duplicate_email(exc):
    return 'users.email' in str(exc.orig)


class UserRepository:
    def get(self, user_id):
        if not fits_db_integer(user_id):
            return None
        return db.session.get(User, user_id)

    def get_by_email(self, email):
        return db.session.execute(select(User).where(User.email == email)).scalars().first()

    def list_with_task_count(self, limit=None, offset=0):
        stmt = (
            select(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return db.session.execute(stmt).all()

    def productivity(self):
        """(id, nome, total de tasks, tasks concluídas) por usuário, numa consulta (T08)."""
        completed = func.coalesce(func.sum(case((Task.status == DONE_STATUS, 1), else_=0)), 0)
        stmt = (
            select(User.id, User.name, func.count(Task.id), completed)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        )
        return db.session.execute(stmt).all()

    def count(self):
        return db.session.scalar(select(func.count(User.id)))

    def add(self, user):
        return self._write(lambda session: session.add(user), user)

    def save(self, user):
        return self._write(lambda session: None, user)

    def delete(self, user):
        with transaction() as session:
            session.delete(user)

    def _write(self, stage, user):
        # O UNIQUE do banco é a garantia; a violação vira o mesmo 409 da checagem prévia (T07).
        try:
            with transaction() as session:
                stage(session)
        except IntegrityError as exc:
            if _is_duplicate_email(exc):
                raise ConflictError(EMAIL_TAKEN_MESSAGE) from exc
            raise
        return user
