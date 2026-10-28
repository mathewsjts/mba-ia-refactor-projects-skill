"""Entry point documentado: `python app.py`.

Expõe `app` no nível do módulo (usado também por `flask --app app ...`) e sobe
o servidor com host/porta/debug vindos da configuração (T02).
"""
from src.app import create_app
from src.config.settings import Settings

settings = Settings.from_env()
app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
