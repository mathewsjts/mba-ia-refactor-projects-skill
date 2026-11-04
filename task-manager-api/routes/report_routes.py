from flask import Blueprint


def register_report_routes(app, controller, auth):
    bp = Blueprint('reports', __name__)
    bp.add_url_rule('/reports/summary', 'summary_report', controller.summary, methods=['GET'])
    bp.add_url_rule('/reports/user/<int:user_id>', 'user_report', auth(controller.user_report), methods=['GET'])
    app.register_blueprint(bp)
