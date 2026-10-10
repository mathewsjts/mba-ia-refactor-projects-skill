"""Autenticação das rotas administrativas (T14).

Falha fechada: sem ADMIN_TOKEN configurado, nenhuma requisição é autorizada.
"""
import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN") or ""
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided, expected):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)

    return wrapper
