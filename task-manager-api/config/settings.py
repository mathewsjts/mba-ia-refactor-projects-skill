"""Configuração lida do ambiente uma única vez, no composition root (T02)."""
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str
    debug: bool
    host: str
    port: int
    secret_key: str
    database_url: str
    cors_origins: object
    token_max_age: int
    log_level: str

    @classmethod
    def from_env(cls, environ=None):
        if environ is None:
            load_dotenv()
            environ = os.environ
        env = environ.get("APP_ENV", "development")
        production = env == "production"

        secret_key = environ.get("SECRET_KEY")
        if not secret_key:
            if production:
                raise RuntimeError("SECRET_KEY é obrigatória em produção")
            # Efêmera: tokens emitidos deixam de valer a cada restart em desenvolvimento.
            secret_key = secrets.token_hex(32)

        origins = environ.get("CORS_ORIGINS")
        if origins:
            cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        else:
            cors_origins = [] if production else "*"

        return cls(
            env=env,
            debug=_as_bool(environ.get("APP_DEBUG", "false")),
            host=environ.get("APP_HOST", "127.0.0.1"),
            port=int(environ.get("PORT", "5000")),
            secret_key=secret_key,
            database_url=environ.get("DATABASE_URL", "sqlite:///tasks.db"),
            cors_origins=cors_origins,
            token_max_age=int(environ.get("TOKEN_MAX_AGE", "86400")),
            log_level=environ.get("LOG_LEVEL", "INFO"),
        )
