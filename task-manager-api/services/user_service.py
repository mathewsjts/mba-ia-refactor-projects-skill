import logging
import re

from controllers.validators import require_payload
from constants import EMAIL_REGEX, MIN_PASSWORD_LENGTH, USER_ROLES
from errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


class UserService:
    def list(self, limit=None, offset=0):
        return User.list_all(limit=limit, offset=offset)

    def task_counts(self):
        return Task.count_by_user()

    def get(self, user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    def tasks_for(self, user_id):
        return Task.list_for_user(user_id)

    def create(self, data):
        require_payload(data)
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "user")

        if not name:
            raise ValidationError("Nome é obrigatório")
        if not email:
            raise ValidationError("Email é obrigatório")
        if not password:
            raise ValidationError("Senha é obrigatória")
        if not re.match(EMAIL_REGEX, email):
            raise ValidationError("Email inválido")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha deve ter no mínimo 4 caracteres")
        if User.get_by_email(email):
            raise ConflictError("Email já cadastrado")
        if role not in USER_ROLES:
            raise ValidationError("Role inválido")

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role
        user.save("Erro ao criar usuário")
        logger.info("Usuário criado: %s - %s", user.id, user.name)
        return user

    def update(self, user_id, data):
        user = self.get(user_id)
        require_payload(data)

        if "name" in data:
            user.name = data["name"]
        if "email" in data:
            if not re.match(EMAIL_REGEX, data["email"]):
                raise ValidationError("Email inválido")
            existing = User.get_by_email(data["email"])
            if existing and existing.id != user_id:
                raise ConflictError("Email já cadastrado")
            user.email = data["email"]
        if "password" in data:
            if len(data["password"]) < MIN_PASSWORD_LENGTH:
                raise ValidationError("Senha muito curta")
            user.set_password(data["password"])
        if "role" in data:
            if data["role"] not in USER_ROLES:
                raise ValidationError("Role inválido")
            user.role = data["role"]
        if "active" in data:
            user.active = data["active"]

        user.save("Erro ao atualizar")
        return user

    def delete(self, user_id):
        user = self.get(user_id)
        user.delete_with_tasks("Erro ao deletar")
        logger.info("Usuário deletado: %s", user_id)

    def authenticate(self, data):
        require_payload(data)
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            raise ValidationError("Email e senha são obrigatórios")

        user = User.get_by_email(email)
        if not user:
            raise UnauthorizedError("Credenciais inválidas")
        if not user.check_password(password):
            raise UnauthorizedError("Credenciais inválidas")
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        return user
