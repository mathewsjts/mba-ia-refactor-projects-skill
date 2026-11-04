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
    database_path: str
    cors_origins: object
    token_max_age: int

    @property
    def production(self):
        return self.env == "production"

    @classmethod
    def from_env(cls, environ=None):
        environ = os.environ if environ is None else environ
        env = environ.get("APP_ENV", "development")
        production = env == "production"

        secret_key = environ.get("SECRET_KEY")
        if not secret_key:
            if production:
                raise RuntimeError("SECRET_KEY é obrigatória em produção")
            # Efêmera: tokens emitidos deixam de valer a cada restart (só desenvolvimento).
            secret_key = secrets.token_hex(32)

        origins = environ.get("CORS_ORIGINS")
        if origins:
            cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        else:
            cors_origins = [] if production else "*"

        return cls(
            env=env,
            debug=_as_bool(environ.get("DEBUG", "false")),
            host=environ.get("HOST", "127.0.0.1"),
            port=int(environ.get("PORT", "5000")),
            secret_key=secret_key,
            database_path=environ.get("DATABASE_PATH", "loja.db"),
            cors_origins=cors_origins,
            token_max_age=int(environ.get("TOKEN_MAX_AGE", "86400")),
        )
