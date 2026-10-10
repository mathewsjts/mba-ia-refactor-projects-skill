"""Emissão de token assinado, substituindo o token falso previsível (T14 / AP-05).

O token deixa de ser `'fake-jwt-token-' + id` e passa a ser assinado com a
SECRET_KEY via itsdangerous (já disponível com o Flask). A chave `token` da
resposta de login é preservada; impor o token nas rotas seria quebra adicional
de contrato e não é aplicada aqui.
"""
from itsdangerous import URLSafeTimedSerializer


class AuthService:
    def __init__(self, secret_key):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")

    def issue_token(self, user):
        return self._serializer.dumps({"user_id": user.id})
