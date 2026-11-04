import hmac

from werkzeug.security import check_password_hash, generate_password_hash

# pbkdf2 fixo: o default do Werkzeug 3 (scrypt) falha em builds de Python sem hashlib.scrypt.
METHOD = "pbkdf2:sha256:600000"
_PREFIXOS_HASH = ("pbkdf2:", "scrypt:")


def hash_password(plain):
    return generate_password_hash(plain, method=METHOD)


def verify_password(stored, plain):
    """Retorna (senha_confere, precisa_regravar).

    Bancos criados antes da refatoração guardam a senha em texto plano: a comparação
    legada usa tempo constante e pede regravação com hash no primeiro login válido.
    """
    if not stored:
        return False, False
    if not stored.startswith(_PREFIXOS_HASH):
        return hmac.compare_digest(stored.encode(), plain.encode()), True
    return check_password_hash(stored, plain), False
