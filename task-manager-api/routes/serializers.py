"""Representação pública das entidades, com campos explícitos (T13).

Cada função reproduz as chaves e os formatos que a rota original devolvia (`str(datetime)`, tags
como lista). A senha não entra em nenhuma whitelist.
"""


def _date(value):
    return str(value) if value else None


def serialize_task(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': _date(task.due_date),
        'tags': task.tags.split(',') if task.tags else [],
    }


def serialize_task_detail(task):
    return {**serialize_task(task), 'overdue': task.is_overdue()}


def serialize_task_listing(task):
    return {
        **serialize_task_detail(task),
        'user_name': task.user.name if task.user else None,
        'category_name': task.category.name if task.category else None,
    }


def serialize_user_task(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': _date(task.due_date),
        'overdue': task.is_overdue(),
    }


def serialize_user(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
    }


def serialize_user_listing(user, task_count):
    return {**serialize_user(user), 'task_count': task_count}


def serialize_user_detail(user, tasks):
    return {**serialize_user(user), 'tasks': [serialize_task(task) for task in tasks]}


def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def serialize_category_listing(category, task_count):
    return {**serialize_category(category), 'task_count': task_count}
