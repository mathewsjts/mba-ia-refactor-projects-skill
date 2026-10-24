"""Serializers com lista explícita de campos públicos (T13). Sem campos sensíveis."""


def _tags(task):
    return task.tags.split(',') if task.tags else []


def _dt(value):
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
        'due_date': _dt(task.due_date),
        'tags': _tags(task),
    }


def serialize_task_with_overdue(task):
    data = serialize_task(task)
    data['overdue'] = task.is_overdue()
    return data


def serialize_task_listed(task):
    data = serialize_task(task)
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def serialize_user_task(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': _dt(task.due_date),
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


def serialize_user_summary(user, task_count):
    data = serialize_user(user)
    data['task_count'] = task_count
    return data


def serialize_user_detail(user, tasks):
    data = serialize_user(user)
    data['tasks'] = [serialize_task(task) for task in tasks]
    return data


def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def serialize_category_summary(category, task_count):
    data = serialize_category(category)
    data['task_count'] = task_count
    return data
