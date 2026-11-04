from functools import wraps

from flask import g, jsonify, request


def require_auth(auth_service, somente_admin=False):
    """Exige `Authorization: Bearer <token>` emitido pelo POST /login.

    Sem token válido responde 401; com `somente_admin`, usuário sem perfil admin recebe 403.
    O usuário autenticado fica em `g.usuario` para as checagens de dono no controller.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            scheme, _, token = request.headers.get("Authorization", "").partition(" ")
            usuario = auth_service.verificar_token(token) if scheme == "Bearer" and token else None
            if usuario is None:
                return jsonify({"erro": "Não autorizado"}), 401
            if somente_admin and not auth_service.eh_admin(usuario):
                return jsonify({"erro": "Acesso negado"}), 403
            g.usuario = usuario
            return view(*args, **kwargs)
        return wrapper
    return decorator
