from flask import Blueprint


def create_category_routes(controller):
    bp = Blueprint("categories", __name__)
    bp.add_url_rule("/categories", "get_categories", controller.index, methods=["GET"])
    bp.add_url_rule("/categories", "create_category", controller.create, methods=["POST"])
    bp.add_url_rule(
        "/categories/<int:category_id>", "update_category", controller.update, methods=["PUT"]
    )
    bp.add_url_rule(
        "/categories/<int:category_id>", "delete_category", controller.delete, methods=["DELETE"]
    )
    return bp
