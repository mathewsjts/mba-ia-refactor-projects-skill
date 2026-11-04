from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from constants import ADMIN_ROLE, DEFAULT_ROLE, MAX_DB_INTEGER
from database import commit, db, paginate
from models.clock import utcnow
from models.passwords import hash_password, verify_password


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, plain):
        self.password = hash_password(plain)

    def check_password(self, plain):
        matches, needs_rehash = verify_password(self.password, plain)
        if matches and needs_rehash:
            self.password = hash_password(plain)
        return matches

    def is_admin(self):
        return self.role == ADMIN_ROLE


class DuplicateEmailError(Exception):
    """O banco recusou o e-mail por violar o índice único (corrida entre duas gravações)."""


def _commit_unique_email():
    try:
        commit()
    except IntegrityError as exc:
        if 'email' in str(exc.orig):
            raise DuplicateEmailError() from exc
        raise


class UserRepository:
    def get(self, user_id):
        if not 0 < user_id <= MAX_DB_INTEGER:
            return None
        return db.session.get(User, user_id)

    def get_by_email(self, email):
        return db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def list(self, limit=None, offset=0):
        return paginate(select(User).order_by(User.id), limit, offset)

    def count(self):
        return db.session.scalar(select(func.count(User.id)))

    def add(self, user):
        db.session.add(user)
        _commit_unique_email()

    def save(self):
        _commit_unique_email()

    def delete(self, user):
        db.session.delete(user)
        commit()
