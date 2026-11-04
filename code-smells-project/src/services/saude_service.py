import logging

logger = logging.getLogger(__name__)


class SaudeService:
    def __init__(self, produto_model, usuario_model, pedido_model):
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model

    def contagens(self):
        """Contagens por tabela, ou None se o banco não responder."""
        try:
            return {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            }
        except Exception:
            logger.exception("Health check: banco indisponível")
            return None
