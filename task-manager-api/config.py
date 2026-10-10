"""Configuração da aplicação lida do ambiente uma única vez (T02)."""
import os
import secrets
from dataclasses import dataclass


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str
    debug: bool
    host: str
    port: int
    secret_key: str
    database_uri: str
    cors_origins: object
    admin_token: str

    @classmethod
    def from_env(cls, environ=None):
        environ = os.environ if environ is None else environ
        env = environ.get("APP_ENV", "development")
        production = env == "production"

        secret_key = environ.get("SECRET_KEY")
        if not secret_key:
            if production:
                raise RuntimeError("SECRET_KEY é obrigatória em produção")
            secret_key = secrets.token_hex(32)

        origins = environ.get("CORS_ORIGINS")
        if origins:
            cors_origins = [o.strip() for o in origins.split(",") if o.strip()]
        else:
            cors_origins = [] if production else "*"

        return cls(
            env=env,
            debug=_as_bool(environ.get("APP_DEBUG", "false")),
            host=environ.get("APP_HOST", "0.0.0.0"),
            port=int(environ.get("PORT", "5000")),
            secret_key=secret_key,
            database_uri=environ.get("DATABASE_URI", "sqlite:///tasks.db"),
            cors_origins=cors_origins,
            admin_token=environ.get("ADMIN_TOKEN", ""),
        )
