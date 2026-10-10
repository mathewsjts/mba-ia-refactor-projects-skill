"""Serviço de notificações (T04).

Abstrai os efeitos de e-mail/SMS/push que o original simulava com `print` dentro
dos handlers HTTP. Hoje é uma implementação de log; pode ser substituída por uma
integração real sem tocar na regra de negócio.
"""
import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("Enviando e-mail/SMS/push de confirmação do pedido %s", pedido_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("Pedido %s aprovado! Preparar envio.", pedido_id)
        if novo_status == "cancelado":
            logger.info("Pedido %s cancelado. Devolver estoque.", pedido_id)
