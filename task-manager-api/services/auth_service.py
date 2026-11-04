from itsdangerous import BadSignature, URLSafeTimedSerializer

from errors import ForbiddenError, UnauthorizedError


class AuthService:
    def __init__(self, user_repository, secret_key, max_age_seconds):
        self._users = user_repository
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age_seconds

    def login(self, email, password):
        user = self._users.get_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        self._users.save()  # persiste a regravação de um hash legado feita por check_password
        return user, self.issue_token(user)

    def issue_token(self, user):
        return self._serializer.dumps({'user_id': user.id})

    def authenticate(self, token):
        """Usuário dono do token, recarregado do banco; None se o token for inválido ou a conta não puder mais entrar."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)  # SignatureExpired herda de BadSignature
        except BadSignature:
            return None
        user_id = payload.get('user_id') if isinstance(payload, dict) else None
        if not isinstance(user_id, int):
            return None
        user = self._users.get(user_id)
        if user is None or not user.active:
            return None
        return user
