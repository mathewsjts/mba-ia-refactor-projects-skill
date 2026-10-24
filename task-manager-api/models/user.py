from database import db
from clock import utcnow
import passwords


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, plain):
        self.password = passwords.hash_password(plain)

    def check_password(self, plain):
        ok, needs_rehash = passwords.verify_password(self.password, plain)
        if ok and needs_rehash:
            self.password = passwords.hash_password(plain)
        return ok

    def is_admin(self):
        return self.role == 'admin'
