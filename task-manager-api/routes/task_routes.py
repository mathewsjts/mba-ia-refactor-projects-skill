from flask import Blueprint


def register_task_routes(app, controller, auth):
    bp = Blueprint('tasks', __name__)
    bp.add_url_rule('/tasks', 'get_tasks', controller.list, methods=['GET'])
    bp.add_url_rule('/tasks/<int:task_id>', 'get_task', controller.show, methods=['GET'])
    bp.add_url_rule('/tasks/search', 'search_tasks', controller.search, methods=['GET'])
    bp.add_url_rule('/tasks/stats', 'task_stats', controller.stats, methods=['GET'])
    # Escrita exige token; dono ou admin é conferido no service.
    bp.add_url_rule('/tasks', 'create_task', auth(controller.create), methods=['POST'])
    bp.add_url_rule('/tasks/<int:task_id>', 'update_task', auth(controller.update), methods=['PUT'])
    bp.add_url_rule('/tasks/<int:task_id>', 'delete_task', auth(controller.delete), methods=['DELETE'])
    app.register_blueprint(bp)
