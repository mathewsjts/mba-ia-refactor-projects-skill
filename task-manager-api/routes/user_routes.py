from flask import Blueprint

from middlewares.auth import optional_auth, require_auth


def create_user_blueprint(controller, auth_service):
    authenticated = require_auth(auth_service)
    bp = Blueprint('users', __name__)
    bp.add_url_rule('/users', 'get_users', authenticated(controller.index), methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', 'get_user', authenticated(controller.show), methods=['GET'])
    bp.add_url_rule('/users', 'create_user', optional_auth(auth_service)(controller.create), methods=['POST'])
    bp.add_url_rule('/users/<int:user_id>', 'update_user', authenticated(controller.update), methods=['PUT'])
    bp.add_url_rule('/users/<int:user_id>', 'delete_user', authenticated(controller.delete), methods=['DELETE'])
    bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', controller.tasks, methods=['GET'])
    bp.add_url_rule('/login', 'login', controller.login, methods=['POST'])
    return bp
