from flask import Blueprint

from middlewares.auth import require_auth


def create_report_blueprint(controller, auth_service):
    bp = Blueprint('reports', __name__)
    bp.add_url_rule('/reports/summary', 'summary_report', controller.summary, methods=['GET'])
    bp.add_url_rule(
        '/reports/user/<int:user_id>', 'user_report',
        require_auth(auth_service)(controller.user_report), methods=['GET'],
    )
    return bp
