"""Hash e verificação de senha com KDF e salt (T05).

Usa pbkdf2:sha256 do Werkzeug — scrypt (padrão do Werkzeug 3) depende de
`hashlib.scrypt`, ausente em builds ligados ao LibreSSL (Python do macOS).
"""
from werkzeug.security import check_password_hash, generate_password_hash

METHOD = "pbkdf2:sha256"


def hash_password(plain):
    return generate_password_hash(plain, method=METHOD)


def verify_password(stored, plain):
    if not stored:
        return False
    return check_password_hash(stored, plain)
