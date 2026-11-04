"""Extensão do SQLAlchemy, preparação do schema e bloco transacional (T07, T15)."""
from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text

from constants import DB_INTEGER_MAX

db = SQLAlchemy()


def fits_db_integer(value):
    return -DB_INTEGER_MAX - 1 <= value <= DB_INTEGER_MAX


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def init_database(app):
    db.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            # SQLite só aplica FOREIGN KEY com o pragma ligado, e ele vale por conexão.
            event.listen(db.engine, "connect", _enable_sqlite_foreign_keys)
        db.create_all()
        # Bancos criados antes do UNIQUE no schema também passam a garantir e-mail único.
        db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email)"))
        db.session.commit()


@contextmanager
def transaction():
    """Commit ao sair do bloco; rollback e repropagação em qualquer exceção."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
