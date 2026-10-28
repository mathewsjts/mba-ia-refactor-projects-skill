"""Regras de negócio de usuários — hash de senha na criação e no login (T05)."""
from src.errors import NotFoundError, UnauthorizedError
from src.models.passwords import hash_password, verify_password


class UsuarioService:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def listar(self, limit=None, offset=0):
        return self._usuarios.listar(limit, offset)

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, nome, email, senha):
        return self._usuarios.criar(nome, email, hash_password(senha))

    def login(self, email, senha):
        usuario = self._usuarios.buscar_por_email(email)
        if usuario is None or not verify_password(usuario["senha"], senha):
            raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
        return usuario
