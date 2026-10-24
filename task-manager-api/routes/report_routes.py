"""View de relatórios e categorias: mapeia rota → controller (T13, T14)."""
from flask import Blueprint

from middlewares.auth import require_auth


def create_report_blueprint(report_controller, category_controller, auth_service):
    bp = Blueprint('reports', __name__)
    bp.add_url_rule('/reports/summary', 'summary_report', report_controller.summary, methods=['GET'])
    bp.add_url_rule('/reports/user/<int:user_id>', 'user_report', report_controller.user_report, methods=['GET'])
    bp.add_url_rule('/categories', 'get_categories', category_controller.index, methods=['GET'])
    bp.add_url_rule('/categories', 'create_category', category_controller.create, methods=['POST'])
    bp.add_url_rule('/categories/<int:cat_id>', 'update_category', category_controller.update, methods=['PUT'])
    bp.add_url_rule(
        '/categories/<int:cat_id>', 'delete_category',
        require_auth(auth_service)(category_controller.delete), methods=['DELETE'],
    )
    return bp
