import re

from constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_PRIORITY,
    DEFAULT_ROLE,
    DEFAULT_TASK_STATUS,
    EMAIL_PATTERN,
    MAX_DB_INTEGER,
    MAX_PAGE_SIZE,
    PASSWORD_MIN_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TASK_STATUSES,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    USER_ROLES,
)
from errors import ValidationError

_EMAIL = re.compile(EMAIL_PATTERN)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)  # True também é int em Python


def _require_object(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')


def _text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


def _title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _status(value):
    if not isinstance(value, str) or value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    if not _is_int(value) or not PRIORITY_MIN <= value <= PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return value


def _reference_id(value, message):
    """Id de usuário/categoria. Valor vazio fica sem vínculo, como o original tratava valores falsos."""
    if not value:
        return None
    if not _is_int(value):
        raise ValidationError(message)
    return value


def _tags(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return ','.join(value)
    raise ValidationError('Tags inválidas')


def _email(value):
    if not isinstance(value, str) or not _EMAIL.match(value):
        raise ValidationError('Email inválido')
    return value


def _role(value):
    if not isinstance(value, str) or value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def _active(value):
    if isinstance(value, bool):
        return value
    if _is_int(value) and value in (0, 1):
        return bool(value)
    raise ValidationError('Valor de active inválido')


def validate_task_create(data):
    _require_object(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    fields = {
        'title': _title(title),
        'description': _text(data.get('description', ''), 'Descrição inválida'),
        'status': _status(data.get('status', DEFAULT_TASK_STATUS)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'category_id': _reference_id(data.get('category_id'), 'Categoria inválida'),
        'tags': _tags(data.get('tags')) if data.get('tags') else None,
        # Formato da data é conferido no service, depois de usuário e categoria, como no original.
        'due_date': data.get('due_date'),
    }
    if 'user_id' in data:
        fields['user_id'] = _reference_id(data['user_id'], 'Usuário inválido')
    return fields


def validate_task_update(data):
    _require_object(data)
    fields = {}
    if 'title' in data:
        fields['title'] = _title(data['title'])
    if 'description' in data:
        fields['description'] = _text(data['description'], 'Descrição inválida')
    if 'status' in data:
        fields['status'] = _status(data['status'])
    if 'priority' in data:
        fields['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _reference_id(data['user_id'], 'Usuário inválido')
    if 'category_id' in data:
        fields['category_id'] = _reference_id(data['category_id'], 'Categoria inválida')
    if 'due_date' in data:
        fields['due_date'] = data['due_date']
    if 'tags' in data:
        fields['tags'] = _tags(data['tags'])
    return fields


def validate_user_create(data):
    _require_object(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    _email(email)
    if not isinstance(password, str):
        raise ValidationError('Senha inválida')
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {PASSWORD_MIN_LENGTH} caracteres')
    return {'name': name, 'email': email, 'password': password, 'role': _role(data.get('role', DEFAULT_ROLE))}


def validate_user_update(data):
    _require_object(data)
    fields = {}
    if 'name' in data:
        if not isinstance(data['name'], str):
            raise ValidationError('Nome inválido')
        fields['name'] = data['name']
    if 'email' in data:
        fields['email'] = _email(data['email'])
    if 'password' in data:
        if not isinstance(data['password'], str):
            raise ValidationError('Senha inválida')
        if len(data['password']) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = data['password']
    if 'role' in data:
        fields['role'] = _role(data['role'])
    if 'active' in data:
        fields['active'] = _active(data['active'])
    return fields


def validate_login(data):
    _require_object(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')
    return email, password


def validate_category_create(data):
    _require_object(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    fields = {'name': name, 'description': _text(data.get('description', ''), 'Descrição inválida')}
    if 'color' in data:
        fields['color'] = _text(data['color'], 'Cor inválida')
    return fields


def validate_category_update(data):
    _require_object(data, allow_empty=True)  # o original aceitava {} sem alterar nada
    fields = {}
    if 'name' in data:
        if not isinstance(data['name'], str):
            raise ValidationError('Nome inválido')
        fields['name'] = data['name']
    if 'description' in data:
        fields['description'] = _text(data['description'], 'Descrição inválida')
    if 'color' in data:
        fields['color'] = _text(data['color'], 'Cor inválida')
    return fields


def _query_int(args, name):
    raw = args.get(name, '')
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')
    if abs(value) > MAX_DB_INTEGER:
        raise ValidationError(f'Parâmetro {name} inválido')
    return value


def parse_search_args(args):
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': _query_int(args, 'priority'),
        'user_id': _query_int(args, 'user_id'),
    }


def parse_pagination(args):
    """Paginação opcional: sem `page` nem `per_page`, a listagem continua completa."""
    if 'page' not in args and 'per_page' not in args:
        return None, 0
    page = _query_int(args, 'page')
    per_page = _query_int(args, 'per_page')
    page = 1 if page is None else page
    per_page = DEFAULT_PAGE_SIZE if per_page is None else per_page
    if page < 1 or per_page < 1 or page > MAX_DB_INTEGER // MAX_PAGE_SIZE:
        raise ValidationError('Parâmetros de paginação inválidos')
    per_page = min(per_page, MAX_PAGE_SIZE)
    return per_page, (page - 1) * per_page
