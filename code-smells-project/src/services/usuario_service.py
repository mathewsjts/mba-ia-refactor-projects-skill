import logging

from src.errors import NaoAutenticadoError, NotFoundError
from src.models.passwords import hash_password, verify_password

logger = logging.getLogger(__name__)

TIPO_PADRAO = "cliente"


class UsuarioService:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def listar(self, limit=None, offset=0):
        return self._usuarios.listar(limit, offset)

    def obter(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def existe(self, usuario_id):
        return self._usuarios.buscar_por_id(usuario_id) is not None

    def criar(self, nome, email, senha):
        # O cadastro público sempre cria cliente; o tipo não vem da requisição.
        usuario_id = self._usuarios.criar(nome, email, hash_password(senha), TIPO_PADRAO)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        # E-mail não é único no schema: vale a primeira conta cuja senha confere, como no original.
        for credencial in self._usuarios.buscar_credenciais_por_email(email):
            confere, precisa_regravar = verify_password(credencial["senha"], senha)
            if not confere:
                continue
            if precisa_regravar:
                self._usuarios.atualizar_senha(credencial["id"], hash_password(senha))
            logger.info("Login bem-sucedido: id=%s", credencial["id"])
            return {chave: credencial[chave] for chave in ("id", "nome", "email", "tipo")}
        logger.info("Login falhou")
        raise NaoAutenticadoError("Email ou senha inválidos", incluir_sucesso=True)
