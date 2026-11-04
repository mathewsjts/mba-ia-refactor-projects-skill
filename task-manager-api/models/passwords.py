"""Hash de senha com KDF e salt; hashes MD5 antigos são aceitos uma vez e regravados (T05)."""
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

_LEGACY_MD5 = re.compile(r"^[a-f0-9]{32}$")
# pbkdf2 explícito: o scrypt padrão do Werkzeug 3 depende de hashlib.scrypt, ausente em builds com LibreSSL.
METHOD = "pbkdf2:sha256:600000"


def hash_password(plain):
    return generate_password_hash(plain, method=METHOD)


def verify_password(stored, plain):
    """Retorna (senha_confere, precisa_regravar)."""
    if stored and _LEGACY_MD5.match(stored):
        legacy = hashlib.md5(plain.encode()).hexdigest()
        return hmac.compare_digest(legacy, stored), True
    return check_password_hash(stored, plain), False
