"""Hash de senha com KDF e salt (T05).

Usa pbkdf2:sha256 do Werkzeug (dependência do Flask). O método scrypt (default do
Werkzeug 3) depende de hashlib.scrypt, ausente em builds ligados a LibreSSL (ex.: o
Python do macOS), então fixamos pbkdf2 para funcionar em qualquer ambiente.
"""
from werkzeug.security import check_password_hash, generate_password_hash

METHOD = "pbkdf2:sha256"


def hash_password(plain):
    return generate_password_hash(plain, method=METHOD)


def verify_password(stored, plain):
    if not stored:
        return False
    return check_password_hash(stored, plain)
