from flask import Blueprint


def register_system_routes(app, controller):
    bp = Blueprint('system', __name__)
    bp.add_url_rule('/health', 'health', controller.health, methods=['GET'])
    bp.add_url_rule('/', 'index', controller.index, methods=['GET'])
    app.register_blueprint(bp)
