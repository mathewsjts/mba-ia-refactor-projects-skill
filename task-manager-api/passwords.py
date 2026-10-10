"""Hash de senha com KDF e salt (T05 / AP-04).

Usa pbkdf2:sha256 do Werkzeug (dependência do Flask). Mantém compatibilidade
com os hashes MD5 legados gravados por seeds antigos, verificando-os sem gravar
o formato antigo de volta.
"""
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

_LEGACY_MD5 = re.compile(r"^[a-f0-9]{32}$")
_METHOD = "pbkdf2:sha256"


def hash_password(plain):
    return generate_password_hash(plain, method=_METHOD)


def verify_password(stored, plain):
    if stored and _LEGACY_MD5.match(stored):
        legacy = hashlib.md5(plain.encode()).hexdigest()
        return hmac.compare_digest(legacy, stored)
    return check_password_hash(stored, plain)
