from flask import Blueprint

from middlewares.auth import require_auth


def create_category_blueprint(controller, auth_service):
    bp = Blueprint('categories', __name__)
    bp.add_url_rule('/categories', 'get_categories', controller.index, methods=['GET'])
    bp.add_url_rule('/categories', 'create_category', controller.create, methods=['POST'])
    bp.add_url_rule('/categories/<int:cat_id>', 'update_category', controller.update, methods=['PUT'])
    bp.add_url_rule(
        '/categories/<int:cat_id>', 'delete_category',
        require_auth(auth_service)(controller.delete), methods=['DELETE'],
    )
    return bp
