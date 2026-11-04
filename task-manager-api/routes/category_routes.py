from flask import Blueprint


def register_category_routes(app, controller, auth):
    bp = Blueprint('categories', __name__)
    bp.add_url_rule('/categories', 'get_categories', controller.list, methods=['GET'])
    # Recurso compartilhado: escrita exige token e perfil admin (conferido no service).
    bp.add_url_rule('/categories', 'create_category', auth(controller.create), methods=['POST'])
    bp.add_url_rule('/categories/<int:category_id>', 'update_category', auth(controller.update), methods=['PUT'])
    bp.add_url_rule('/categories/<int:category_id>', 'delete_category', auth(controller.delete), methods=['DELETE'])
    app.register_blueprint(bp)
