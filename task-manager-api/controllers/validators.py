"""Validação de entrada reutilizável, com as mesmas mensagens e ordem do original (T09)."""
import re

from errors import ValidationError
from constants import (
    DEFAULT_PRIORITY,
    EMAIL_REGEX,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TASK_STATUSES,
)


def validate_task_create(data):
    if not data:
        raise ValidationError('Dados inválidos')
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    status = data.get('status', 'pending')
    priority = data.get('priority', DEFAULT_PRIORITY)
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return {
        'title': title,
        'description': data.get('description', ''),
        'status': status,
        'priority': priority,
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
        'due_date': data.get('due_date'),
        'tags': data.get('tags'),
    }


def validate_user_create(data):
    if not data:
        raise ValidationError('Dados inválidos')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not re.match(EMAIL_REGEX, email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    return {'name': name, 'email': email, 'password': password, 'role': role}
