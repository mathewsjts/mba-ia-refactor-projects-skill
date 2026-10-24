"""Emissão e verificação de token assinado (T14). Usa itsdangerous, que acompanha o Flask."""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class AuthService:
    def __init__(self, secret_key, max_age_seconds=86400):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age_seconds

    def issue_token(self, user):
        return self._serializer.dumps({'user_id': user.id})

    def verify_token(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
