import logging

from constants import ADMIN_ROLE, DEFAULT_ROLE
from errors import ConflictError, ForbiddenError, NotFoundError
from models.user import DuplicateEmailError, User
from services.authorization import ensure_admin, ensure_owner_or_admin

logger = logging.getLogger(__name__)

EMAIL_TAKEN = 'Email já cadastrado'


class UserService:
    def __init__(self, user_repository, task_repository):
        self._users = user_repository
        self._tasks = task_repository

    def list(self, actor, limit=None, offset=0):
        ensure_admin(actor)
        users = self._users.list(limit, offset)
        task_counts = self._tasks.count_by_user()
        return [(user, task_counts.get(user.id, 0)) for user in users]

    def get(self, user_id):
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user

    def get_own_or_admin(self, actor, user_id):
        user = self.get(user_id)                          # 404 antes do 403
        ensure_owner_or_admin(actor, user.id)
        return user

    def get_detail(self, actor, user_id):
        user = self.get_own_or_admin(actor, user_id)
        return user, self._tasks.list_by_user(user.id)

    def list_tasks(self, user_id):
        user = self.get(user_id)
        return self._tasks.list_by_user(user.id)

    def register(self, actor, fields):
        # Cadastro público: o perfil enviado só vale quando quem chama é admin.
        role = fields.get('role', DEFAULT_ROLE) if actor is not None and actor.is_admin() else DEFAULT_ROLE
        return self._create(fields, role)

    def create_admin(self, fields):
        return self._create(fields, ADMIN_ROLE)

    def update(self, actor, user, fields):
        if ('role' in fields or 'active' in fields) and not actor.is_admin():
            raise ForbiddenError('Acesso negado')
        if 'password' in fields and actor.id != user.id:
            raise ForbiddenError('Acesso negado')         # só o próprio usuário troca a própria senha
        if 'email' in fields:
            existing = self._users.get_by_email(fields['email'])
            if existing is not None and existing.id != user.id:
                raise ConflictError(EMAIL_TAKEN)

        for name in ('name', 'email', 'role', 'active'):
            if name in fields:
                setattr(user, name, fields[name])
        if 'password' in fields:
            user.set_password(fields['password'])
        try:
            self._users.save()
        except DuplicateEmailError:
            raise ConflictError(EMAIL_TAKEN)              # outra requisição gravou o e-mail depois da checagem
        return user

    def delete(self, actor, user_id):
        user = self.get_own_or_admin(actor, user_id)
        self._users.delete(user)                          # as tasks saem pela cascata do relacionamento
        logger.info('Usuário deletado: %s', user_id)

    def _create(self, fields, role):
        if self._users.get_by_email(fields['email']) is not None:
            raise ConflictError(EMAIL_TAKEN)
        user = User(name=fields['name'], email=fields['email'], role=role)
        user.set_password(fields['password'])
        try:
            self._users.add(user)
        except DuplicateEmailError:
            raise ConflictError(EMAIL_TAKEN)              # outra requisição gravou o e-mail depois da checagem
        logger.info('Usuário criado: %s', user.id)
        return user
