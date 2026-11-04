import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_CORS_ORIGINS = ('http://localhost:3000', 'http://127.0.0.1:3000')
DEFAULT_TOKEN_MAX_AGE_SECONDS = 24 * 60 * 60


def _as_bool(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _as_list(value):
    return tuple(item.strip() for item in value.split(',') if item.strip())


@dataclass(frozen=True)
class Settings:
    env: str
    debug: bool
    host: str
    port: int
    secret_key: str
    secret_key_is_ephemeral: bool
    database_url: str
    cors_origins: tuple
    token_max_age: int

    @classmethod
    def from_env(cls, environ=None):
        if environ is None:
            load_dotenv()
            environ = os.environ
        env = environ.get('APP_ENV', 'development')
        production = env == 'production'

        secret_key = environ.get('SECRET_KEY', '')
        if not secret_key and production:
            raise RuntimeError('SECRET_KEY é obrigatória em produção')

        origins = environ.get('CORS_ORIGINS')
        cors_origins = _as_list(origins) if origins else DEFAULT_CORS_ORIGINS

        return cls(
            env=env,
            debug=_as_bool(environ.get('FLASK_DEBUG', 'false')),
            host=environ.get('HOST', '127.0.0.1'),
            port=int(environ.get('PORT', '5000')),
            secret_key=secret_key or secrets.token_hex(32),
            secret_key_is_ephemeral=not secret_key,
            database_url=environ.get('DATABASE_URL', 'sqlite:///tasks.db'),
            cors_origins=cors_origins,
            token_max_age=int(environ.get('TOKEN_MAX_AGE_SECONDS', str(DEFAULT_TOKEN_MAX_AGE_SECONDS))),
        )
