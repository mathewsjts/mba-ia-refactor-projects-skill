"""Configuração central (T02): lê o ambiente uma única vez, com defaults seguros.

Nenhum segredo literal vive aqui. Em produção, segredos ausentes falham no boot;
em desenvolvimento, a SECRET_KEY recebe um valor aleatório efêmero.
"""
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
    admin_token: str
    database_path: str
    cors_origins: object

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
            host=environ.get("APP_HOST", "127.0.0.1"),
            # Mesmo default do original (5000) para preservar o comando documentado.
            port=int(environ.get("PORT", "5000")),
            secret_key=secret_key,
            admin_token=environ.get("ADMIN_TOKEN", ""),
            # Mesmo arquivo do original para preservar o estado/boot documentado.
            database_path=environ.get("DATABASE_PATH", "loja.db"),
            cors_origins=cors_origins,
        )
