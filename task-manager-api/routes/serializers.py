"""Representação pública das entidades. Só os campos listados aqui saem nas respostas."""


def _date_or_none(value):
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
        'due_date': _date_or_none(task.due_date),
        'tags': task.tags.split(',') if task.tags else [],
    }


def serialize_task_detail(task):
    data = serialize_task(task)
    data['overdue'] = task.is_overdue()
    return data


def serialize_task_with_relations(task):
    data = serialize_task_detail(task)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def serialize_task_summary(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': _date_or_none(task.due_date),
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


def serialize_user_with_task_count(user, task_count):
    data = serialize_user(user)
    data['task_count'] = task_count
    return data


def serialize_user_detail(user, tasks):
    data = serialize_user(user)
    data['tasks'] = [serialize_task(task) for task in tasks]
    return data


def serialize_user_report(user, statistics):
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': statistics,
    }


def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def serialize_category_with_task_count(category, task_count):
    data = serialize_category(category)
    data['task_count'] = task_count
    return data


def serialize_summary(report):
    data = dict(report)
    data['generated_at'] = str(report['generated_at'])
    data['overdue'] = {
        'count': len(report['overdue']),
        'tasks': [
            {'id': task.id, 'title': task.title, 'due_date': str(task.due_date), 'days_overdue': days}
            for task, days in report['overdue']
        ],
    }
    return data
