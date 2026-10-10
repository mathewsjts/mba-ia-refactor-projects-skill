"""Regras de usuário e autenticação (T04, T05)."""
from src.errors import NotFoundError, UnauthorizedError
from src.models.passwords import hash_password, verify_password


class UsuarioService:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, nome, email, senha):
        return self._usuarios.criar(nome, email, hash_password(senha))

    def autenticar(self, email, senha):
        usuario = self._usuarios.buscar_por_email(email)
        if usuario and verify_password(usuario["senha"], senha):
            return {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "tipo": usuario["tipo"],
            }
        raise UnauthorizedError("Email ou senha inválidos", include_sucesso=True)
