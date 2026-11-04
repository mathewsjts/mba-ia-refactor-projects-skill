class AppError(Exception):
    status_code = 500
    # Algumas respostas de erro do contrato original trazem "sucesso": false, outras não.
    incluir_sucesso = False

    def __init__(self, mensagem, incluir_sucesso=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if incluir_sucesso is not None:
            self.incluir_sucesso = incluir_sucesso


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class RegraNegocioError(AppError):
    status_code = 400
    incluir_sucesso = True


class NaoAutenticadoError(AppError):
    status_code = 401


class AcessoNegadoError(AppError):
    status_code = 403
