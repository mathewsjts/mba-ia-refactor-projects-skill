import logging

from constants import ADMIN_ROLE, DEFAULT_ROLE, EMAIL_TAKEN_MESSAGE, USER_NOT_FOUND_MESSAGE
from errors import ConflictError, ForbiddenError, NotFoundError
from models.user import User

logger = logging.getLogger(__name__)

PRIVILEGED_FIELDS = frozenset({"role", "active"})
FORBIDDEN_MESSAGE = "Acesso negado"


class UserService:
    def __init__(self, user_repository, task_repository):
        self._users = user_repository
        self._tasks = task_repository

    def list_users(self, limit=None, offset=0):
        return self._users.list_with_task_count(limit, offset)

    def get(self, user_id):
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError(USER_NOT_FOUND_MESSAGE)
        return user

    def get_with_tasks(self, user_id):
        user = self.get(user_id)
        return user, self._tasks.list_by_user(user_id)

    def get_user_tasks(self, user_id):
        return self.get_with_tasks(user_id)[1]

    def ensure_email_available(self, email, exclude_id=None):
        """Checagem prévia, só para a mensagem; a garantia é o UNIQUE no banco (UserRepository)."""
        existing = self._users.get_by_email(email)
        if existing is not None and existing.id != exclude_id:
            raise ConflictError(EMAIL_TAKEN_MESSAGE)

    def create(self, fields, actor=None):
        # Cadastro público grava o perfil padrão; só um admin autenticado escolhe o perfil (T14).
        role = fields["role"] if actor is not None and actor.is_admin() else DEFAULT_ROLE
        return self._create(fields, role)

    def create_admin(self, fields):
        return self._create(fields, ADMIN_ROLE)

    def _create(self, fields, role):
        user = User(name=fields["name"], email=fields["email"], role=role)
        user.set_password(fields["password"])
        user = self._users.add(user)
        logger.info("Usuário criado: %s - %s", user.id, user.name)
        return user

    def authorize_update(self, actor, user, requested_fields):
        """Só o próprio usuário altera a própria conta; perfil, estado e contas alheias exigem admin."""
        if actor.is_admin():
            return
        if actor.id != user.id or PRIVILEGED_FIELDS & set(requested_fields):
            raise ForbiddenError(FORBIDDEN_MESSAGE)

    def update(self, user, fields):
        for name, value in fields.items():
            if name == "password":
                user.set_password(value)
            else:
                setattr(user, name, value)
        return self._users.save(user)

    def delete(self, actor, user_id):
        user = self.get(user_id)
        if not actor.is_admin() and actor.id != user.id:
            raise ForbiddenError(FORBIDDEN_MESSAGE)
        self._users.delete(user)
        logger.info("Usuário deletado: %s", user_id)
