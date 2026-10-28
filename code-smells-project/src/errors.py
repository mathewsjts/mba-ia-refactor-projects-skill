"""Erros de domínio, traduzidos para HTTP pelo middleware central (T10)."""


class AppError(Exception):
    """Erro de domínio com status HTTP associado.

    `sucesso` controla se a chave `sucesso: false` acompanha a resposta de erro
    — o contrato original é inconsistente (alguns 404/401 trazem `sucesso`,
    outros erros só `erro`), então cada ponto que levanta o erro decide.
    """

    status_code = 500

    def __init__(self, message, *, sucesso=None):
        super().__init__(message)
        self.message = message
        self.sucesso = sucesso

    def to_body(self):
        body = {"erro": self.message}
        if self.sucesso is not None:
            body["sucesso"] = self.sucesso
        return body


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401
