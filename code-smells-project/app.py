import logging

from src.app import create_app
from src.config.settings import Settings

settings = Settings.from_env()
app = create_app(settings)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
