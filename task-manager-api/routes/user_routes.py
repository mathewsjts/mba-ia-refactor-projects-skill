from flask import Blueprint


def register_user_routes(app, controller, auth, optional_auth):
    bp = Blueprint('users', __name__)
    # Leituras com e-mail exigem token; admin ou a própria conta é conferido no service.
    bp.add_url_rule('/users', 'get_users', auth(controller.list), methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', 'get_user', auth(controller.show), methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', controller.tasks, methods=['GET'])
    # Públicas: login e cadastro (sem token de admin, o perfil enviado é ignorado).
    bp.add_url_rule('/login', 'login', controller.login, methods=['POST'])
    bp.add_url_rule('/users', 'create_user', optional_auth(controller.create), methods=['POST'])
    bp.add_url_rule('/users/<int:user_id>', 'update_user', auth(controller.update), methods=['PUT'])
    bp.add_url_rule('/users/<int:user_id>', 'delete_user', auth(controller.delete), methods=['DELETE'])
    app.register_blueprint(bp)
