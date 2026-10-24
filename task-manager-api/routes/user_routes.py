"""View de usuários e login: mapeia rota → controller (T13, T14)."""
from flask import Blueprint

from middlewares.auth import require_auth


def create_user_blueprint(controller, auth_service):
    bp = Blueprint('users', __name__)
    bp.add_url_rule('/users', 'get_users', controller.index, methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', 'get_user', controller.show, methods=['GET'])
    bp.add_url_rule('/users', 'create_user', controller.create, methods=['POST'])
    bp.add_url_rule('/users/<int:user_id>', 'update_user', controller.update, methods=['PUT'])
    bp.add_url_rule(
        '/users/<int:user_id>', 'delete_user',
        require_auth(auth_service)(controller.delete), methods=['DELETE'],
    )
    bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', controller.user_tasks, methods=['GET'])
    bp.add_url_rule('/login', 'login', controller.login, methods=['POST'])
    return bp
