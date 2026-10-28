"""Integrações de notificação (e-mail/SMS/push) — saem da camada HTTP (T04).

Simuladas por log; no original eram `print` dentro dos handlers. Trocar o log
por um provedor real é uma mudança isolada aqui, sem tocar controllers.
"""
import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        elif novo_status == "cancelado":
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
