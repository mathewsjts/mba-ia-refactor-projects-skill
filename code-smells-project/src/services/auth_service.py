from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.errors import AcessoNegadoError

PERFIL_ADMIN = "admin"


class AuthService:
    def __init__(self, secret_key, max_age_seconds, usuario_model):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age_seconds
        self._usuarios = usuario_model

    def emitir_token(self, usuario):
        return self._serializer.dumps({"usuario_id": usuario["id"]})

    def verificar_token(self, token):
        """Usuário dono do token, ou None se o token for inválido, expirado ou órfão."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        # O perfil vem do banco a cada requisição: rebaixar ou apagar o usuário vale na hora.
        return self._usuarios.buscar_por_id(payload.get("usuario_id"))

    @staticmethod
    def eh_admin(usuario):
        return usuario is not None and usuario["tipo"] == PERFIL_ADMIN

    def garantir_dono_ou_admin(self, usuario, usuario_id):
        if not (self.eh_admin(usuario) or usuario["id"] == usuario_id):
            raise AcessoNegadoError("Acesso negado")
