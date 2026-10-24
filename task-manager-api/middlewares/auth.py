"""Exige token assinado nas rotas destrutivas/privilegiadas (T14)."""
from functools import wraps

from flask import g, jsonify, request


def require_auth(auth_service):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            scheme, _, token = request.headers.get('Authorization', '').partition(' ')
            payload = auth_service.verify_token(token) if scheme == 'Bearer' and token else None
            if payload is None:
                return jsonify({'error': 'Não autorizado'}), 401
            g.user_id = payload['user_id']
            return view(*args, **kwargs)
        return wrapper
    return decorator
