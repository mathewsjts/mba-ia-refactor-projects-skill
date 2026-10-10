"""Erros de domínio — módulo neutro importado por services, controllers e middlewares."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, include_sucesso=False):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        # O original respondia alguns erros com a chave extra "sucesso": False
        # e outros só com "erro". Preservamos exatamente esse contrato por caso.
        self.include_sucesso = include_sucesso

    def to_body(self):
        body = {"erro": self.message}
        if self.include_sucesso:
            body["sucesso"] = False
        return body


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401
