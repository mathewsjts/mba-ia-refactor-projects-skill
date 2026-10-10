"""Entry point documentado (`python app.py`).

Invólucro fino: cria a configuração, monta a aplicação via composition root e, quando
executado diretamente, sobe o servidor. Expõe `app` para `flask --app app run`.
"""
import logging

from src.app import create_app
from src.config.settings import Settings

logger = logging.getLogger(__name__)

settings = Settings.from_env()
app = create_app(settings)

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
