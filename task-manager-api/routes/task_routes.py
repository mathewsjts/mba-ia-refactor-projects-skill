"""View de tarefas: mapeia rota → controller (T13, T14)."""
from flask import Blueprint

from middlewares.auth import require_auth


def create_task_blueprint(controller, auth_service):
    bp = Blueprint('tasks', __name__)
    bp.add_url_rule('/tasks', 'get_tasks', controller.index, methods=['GET'])
    bp.add_url_rule('/tasks/search', 'search_tasks', controller.search, methods=['GET'])
    bp.add_url_rule('/tasks/stats', 'task_stats', controller.stats, methods=['GET'])
    bp.add_url_rule('/tasks/<int:task_id>', 'get_task', controller.show, methods=['GET'])
    bp.add_url_rule('/tasks', 'create_task', controller.create, methods=['POST'])
    bp.add_url_rule('/tasks/<int:task_id>', 'update_task', controller.update, methods=['PUT'])
    bp.add_url_rule(
        '/tasks/<int:task_id>', 'delete_task',
        require_auth(auth_service)(controller.delete), methods=['DELETE'],
    )
    return bp
