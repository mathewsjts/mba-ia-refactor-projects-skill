"""Regras de negócio de usuários e autenticação de login (T04, T14)."""
import re

from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.user import User
from constants import EMAIL_REGEX, MIN_PASSWORD_LENGTH, USER_ROLES


class UserService:
    def __init__(self, user_repository, task_repository, auth_service):
        self._users = user_repository
        self._tasks = task_repository
        self._auth = auth_service

    def list_users(self):
        users = self._users.list_all()
        counts = self._users.task_counts()
        return [(user, counts.get(user.id, 0)) for user in users]

    def get_user(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def get_user_with_tasks(self, user_id):
        user = self.get_user(user_id)
        return user, self._tasks.list_by_user(user_id)

    def create_user(self, validated):
        if self._users.get_by_email(validated['email']):
            raise ConflictError('Email já cadastrado')
        if validated['role'] not in USER_ROLES:
            raise ValidationError('Role inválido')
        user = User()
        user.name = validated['name']
        user.email = validated['email']
        user.set_password(validated['password'])
        user.role = validated['role']
        self._users.add(user)
        db.session.commit()
        return user

    def update_user(self, user_id, data):
        user = self.get_user(user_id)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            if not re.match(EMAIL_REGEX, data['email']):
                raise ValidationError('Email inválido')
            existing = self._users.get_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])
        if 'role' in data:
            if data['role'] not in USER_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        self._users.delete(user)
        db.session.commit()

    def login(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        user = self._users.get_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        db.session.commit()  # persiste eventual re-hash de senha legada
        return user, self._auth.issue_token(user)
