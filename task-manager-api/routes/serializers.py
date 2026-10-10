"""Serialização pública das entidades, com campos explícitos (T13).

Campos sensíveis (senha/hash) não entram na whitelist — remoção declarada em
BC-01. Cada formato público do baseline tem aqui uma função dedicada.
"""


def serialize_task(task):
    """Formato base da Task (equivalente ao antigo Task.to_dict)."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "user_id": task.user_id,
        "category_id": task.category_id,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
        "due_date": str(task.due_date) if task.due_date else None,
        "tags": task.tags.split(",") if task.tags else [],
    }


def serialize_task_detail(task):
    """GET /tasks/<id>: base + overdue."""
    data = serialize_task(task)
    data["overdue"] = task.is_overdue()
    return data


def serialize_task_enriched(task):
    """GET /tasks: base + overdue + nomes de usuário e categoria."""
    data = serialize_task(task)
    data["overdue"] = task.is_overdue()
    data["user_name"] = task.user.name if task.user else None
    data["category_name"] = task.category.name if task.category else None
    return data


def serialize_task_summary(task):
    """GET /users/<id>/tasks: subconjunto de campos + overdue."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "created_at": str(task.created_at),
        "due_date": str(task.due_date) if task.due_date else None,
        "overdue": task.is_overdue(),
    }


def serialize_user(user):
    """Formato público do usuário — sem a senha (BC-01)."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "active": user.active,
        "created_at": str(user.created_at),
    }


def serialize_user_list(user, task_count):
    data = serialize_user(user)
    data["task_count"] = task_count
    return data


def serialize_user_detail(user, tasks):
    data = serialize_user(user)
    data["tasks"] = [serialize_task(task) for task in tasks]
    return data


def serialize_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "created_at": str(category.created_at),
    }


def serialize_category_list(category, task_count):
    data = serialize_category(category)
    data["task_count"] = task_count
    return data
