import logging


class NotificacaoService:
    """Notificações de pedido. Hoje só registra em log; um envio real (e-mail, SMS, push)
    entra aqui sem tocar na regra do pedido."""

    def __init__(self, logger=None):
        self._logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self._logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        self._logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        self._logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id, status):
        if status == "aprovado":
            self._logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        elif status == "cancelado":
            self._logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
