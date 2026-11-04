from functools import wraps

from flask import g, request

from errors import UnauthorizedError


def _current_user(auth_service):
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme != 'Bearer' or not token:
        return None
    return auth_service.authenticate(token)


def require_auth(auth_service):
    """Exige `Authorization: Bearer <token>`; o usuário é recarregado do banco e fica em `g.user`."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _current_user(auth_service)
            if user is None:
                raise UnauthorizedError('Não autorizado')
            g.user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator


def optional_auth(auth_service):
    """Para rotas públicas que mudam de comportamento com um admin autenticado (cadastro)."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.user = _current_user(auth_service)
            return view(*args, **kwargs)
        return wrapper
    return decorator
