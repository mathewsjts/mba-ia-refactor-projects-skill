from errors import ForbiddenError


def ensure_owner_or_admin(actor, owner_id):
    if not actor.is_admin() and actor.id != owner_id:
        raise ForbiddenError('Acesso negado')


def ensure_admin(actor):
    if not actor.is_admin():
        raise ForbiddenError('Acesso negado')
