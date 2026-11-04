from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from errors import ForbiddenError, UnauthorizedError


class AuthService:
    """Login com token assinado; o token prova só quem fez login, e quando (T14)."""

    def __init__(self, user_repository, secret_key, max_age_seconds):
        self._users = user_repository
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age_seconds

    def login(self, email, password):
        user = self._users.get_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError("Credenciais inválidas")
        # check_password pode ter regravado um hash legado: persiste antes de seguir.
        self._users.save(user)
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        return user, self.issue_token(user)

    def issue_token(self, user):
        return self._serializer.dumps({"user_id": user.id})

    def authenticate(self, token):
        """Usuário atual do token, recarregado do banco: conta apagada ou inativa perde o acesso."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        user_id = payload.get("user_id") if isinstance(payload, dict) else None
        if not isinstance(user_id, int):
            return None
        user = self._users.get(user_id)
        if user is None or not user.active:
            return None
        return user
