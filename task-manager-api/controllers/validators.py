"""Validadores de entrada (T09).

Mesmas mensagens e mesma ordem de verificação das rotas originais. Entrada de tipo errado, que no
original virava 500, vira 400. Checagens que dependem do banco (usuário, categoria, e-mail) chegam
como callbacks do service e rodam no mesmo ponto da sequência original.
"""
import re
from datetime import datetime

from constants import (
    CATEGORY_NOT_FOUND_MESSAGE,
    DB_INTEGER_MAX,
    DEFAULT_CATEGORY_COLOR,
    DEFAULT_PRIORITY,
    DEFAULT_ROLE,
    DEFAULT_TASK_STATUS,
    DUE_DATE_FORMAT,
    EMAIL_PATTERN,
    MAX_PAGE_SIZE,
    PASSWORD_MIN_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TASK_STATUSES,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    USER_NOT_FOUND_MESSAGE,
    USER_ROLES,
)
from errors import NotFoundError, ValidationError

_EMAIL = re.compile(EMAIL_PATTERN)


def _is_int(value):
    # bool é subclasse de int em Python; NaN e Infinity chegam como float e também ficam de fora.
    return isinstance(value, int) and not isinstance(value, bool)


def require_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def _check_optional_text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


# ---------------------------------------------------------------- paginação e query

def parse_pagination(args):
    """Paginação opcional (T17): sem `limit`, a listagem vem completa, como antes."""
    if 'limit' not in args:
        return None, 0
    try:
        limit = int(args['limit'])
        offset = int(args.get('offset', 0))
    except ValueError:
        raise ValidationError('Parâmetros de paginação inválidos')
    if limit < 0 or not 0 <= offset <= DB_INTEGER_MAX:
        raise ValidationError('Parâmetros de paginação inválidos')
    return min(limit, MAX_PAGE_SIZE), offset


def _query_int(raw, message):
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(message)
    if not -DB_INTEGER_MAX <= value <= DB_INTEGER_MAX:
        raise ValidationError(message)
    return value


def parse_task_search(args):
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': _query_int(priority, 'Parâmetro priority inválido') if priority else None,
        'user_id': _query_int(user_id, 'Parâmetro user_id inválido') if user_id else None,
    }


# ---------------------------------------------------------------- tasks

def _check_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _check_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _check_priority(priority):
    if not _is_int(priority) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def _reference_id(value, not_found_message, ensure_exists):
    """Id de usuário/categoria do corpo. Vazio = sem vínculo; id que não pode existir = 404, como no original."""
    if not value:
        return None
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if not _is_int(value) or not 0 < value <= DB_INTEGER_MAX:
        raise NotFoundError(not_found_message)
    ensure_exists(value)
    return value


def _parse_due_date(value, message):
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(message)


def _join_tags(tags):
    if tags is None or isinstance(tags, str):
        return tags
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return ','.join(tags)
    raise ValidationError('Tags inválidas')


def validate_task_create(data, ensure_user, ensure_category):
    require_object(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    _check_title(title)

    description = data.get('description', '')
    status = _check_status(data.get('status', DEFAULT_TASK_STATUS))
    priority = _check_priority(data.get('priority', DEFAULT_PRIORITY))
    user_id = _reference_id(data.get('user_id'), USER_NOT_FOUND_MESSAGE, ensure_user)
    category_id = _reference_id(data.get('category_id'), CATEGORY_NOT_FOUND_MESSAGE, ensure_category)

    due_date = data.get('due_date')
    if due_date:
        due_date = _parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
    else:
        due_date = None
    tags = data.get('tags')
    tags = _join_tags(tags) if tags else None
    _check_optional_text(description, 'Descrição inválida')

    return {
        'title': title,
        'description': description,
        'status': status,
        'priority': priority,
        'user_id': user_id,
        'category_id': category_id,
        'due_date': due_date,
        'tags': tags,
    }


def validate_task_update(data, ensure_user, ensure_category):
    require_object(data)
    fields = {}
    if 'title' in data:
        fields['title'] = _check_title(data['title'])
    if 'description' in data:
        fields['description'] = _check_optional_text(data['description'], 'Descrição inválida')
    if 'status' in data:
        fields['status'] = _check_status(data['status'])
    if 'priority' in data:
        fields['priority'] = _check_priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _reference_id(data['user_id'], USER_NOT_FOUND_MESSAGE, ensure_user)
    if 'category_id' in data:
        fields['category_id'] = _reference_id(data['category_id'], CATEGORY_NOT_FOUND_MESSAGE, ensure_category)
    if 'due_date' in data:
        due_date = data['due_date']
        fields['due_date'] = _parse_due_date(due_date, 'Formato de data inválido') if due_date else None
    if 'tags' in data:
        fields['tags'] = _join_tags(data['tags'])
    return fields


# ---------------------------------------------------------------- usuários e login

def _check_email(email):
    if not isinstance(email, str) or not _EMAIL.match(email):
        raise ValidationError('Email inválido')
    return email


def _check_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_create(data, ensure_email_available):
    require_object(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    _check_email(email)
    if not isinstance(password, str):
        raise ValidationError('Senha inválida')
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    ensure_email_available(email)
    _check_role(role)
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_user_update(data, ensure_email_available):
    require_object(data)
    fields = {}
    if 'name' in data:
        if not isinstance(data['name'], str):
            raise ValidationError('Nome inválido')
        fields['name'] = data['name']
    if 'email' in data:
        fields['email'] = _check_email(data['email'])
        ensure_email_available(data['email'])
    if 'password' in data:
        if not isinstance(data['password'], str):
            raise ValidationError('Senha inválida')
        if len(data['password']) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = data['password']
    if 'role' in data:
        fields['role'] = _check_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active inválido')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    require_object(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha devem ser texto')
    return email, password


# ---------------------------------------------------------------- categorias

def validate_category_create(data):
    require_object(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    return {
        'name': name,
        'description': _check_optional_text(data.get('description', ''), 'Descrição inválida'),
        'color': _check_optional_text(data.get('color', DEFAULT_CATEGORY_COLOR), 'Cor inválida'),
    }


def validate_category_update(data):
    # O original aceitava `{}` na atualização de categoria (200 sem mudanças); só não-objeto é recusado.
    if not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    fields = {}
    if 'name' in data:
        if not isinstance(data['name'], str):
            raise ValidationError('Nome inválido')
        fields['name'] = data['name']
    if 'description' in data:
        fields['description'] = _check_optional_text(data['description'], 'Descrição inválida')
    if 'color' in data:
        fields['color'] = _check_optional_text(data['color'], 'Cor inválida')
    return fields
