"""Autenticação por `Authorization: Bearer <token>` (T14)."""
from functools import wraps

from flask import g, request

from errors import UnauthorizedError


def _bearer_token():
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    return token if scheme == 'Bearer' and token else None


def _current_user(auth_service):
    token = _bearer_token()
    return auth_service.authenticate(token) if token else None


def require_auth(auth_service):
    """Recusa com 401 sem token válido de uma conta existente e ativa; expõe o usuário em `g.current_user`."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _current_user(auth_service)
            if user is None:
                raise UnauthorizedError('Não autorizado')
            g.current_user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator


def optional_auth(auth_service):
    """Rota pública que muda de comportamento para quem está autenticado (ex.: admin escolhe o perfil)."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = _current_user(auth_service)
            return view(*args, **kwargs)
        return wrapper
    return decorator
