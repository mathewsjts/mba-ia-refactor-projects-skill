"""Hash de senha com KDF e salt (substitui MD5 — T05)."""
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

_LEGACY_MD5 = re.compile(r"^[a-f0-9]{32}$")
METHOD = "pbkdf2:sha256:600000"


def hash_password(plain):
    return generate_password_hash(plain, method=METHOD)


def verify_password(stored, plain):
    """Retorna (senha_confere, precisa_regravar)."""
    if stored and _LEGACY_MD5.match(stored):
        legacy = hashlib.md5(plain.encode()).hexdigest()
        return hmac.compare_digest(legacy, stored), True
    return check_password_hash(stored, plain), False
