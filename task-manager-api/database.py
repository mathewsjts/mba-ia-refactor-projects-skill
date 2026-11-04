from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text

db = SQLAlchemy()


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


def init_database(app):
    """Liga a extensão ao app, aplica FKs no SQLite e garante o schema."""
    db.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == 'sqlite':
            event.listen(db.engine, 'connect', _enable_sqlite_foreign_keys)
        db.create_all()
        # Bancos criados antes da refatoração também ganham a garantia de e-mail único.
        db.session.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)'))
        db.session.commit()


def commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def paginate(query, limit=None, offset=0):
    if limit is not None:
        query = query.limit(limit).offset(offset)
    return db.session.execute(query).scalars().all()
