from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from errors import AppError

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """Garante integridade referencial no SQLite (T15 / AP-18)."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # Outros engines não têm esse PRAGMA; ignorar silenciosamente.
        pass


def commit(error_message="Erro interno"):
    """Confirma a sessão atual, fazendo rollback e traduzindo falhas (T10)."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AppError(error_message)
