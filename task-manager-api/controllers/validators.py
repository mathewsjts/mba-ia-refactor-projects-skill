"""Validadores reutilizáveis, compartilhados entre criação e atualização (T09).

Preservam exatamente as mensagens e a ordem de verificação do código original.
"""
from datetime import datetime

from constants import (
    MAX_PAGE_SIZE,
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TASK_STATUSES,
)
from errors import ValidationError


def require_payload(data):
    if not data:
        raise ValidationError("Dados inválidos")


def validate_title(title, required=True):
    if required and not title:
        raise ValidationError("Título é obrigatório")
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError("Status inválido")
    return status


def validate_priority(priority):
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    return priority


def parse_due_date(value, message):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(message)


def normalize_tags(tags):
    if isinstance(tags, list):
        return ",".join(tags)
    return tags


def pagination_args(args):
    """Paginação opt-in (T17): sem `limit`, devolve (None, 0) e nada muda."""
    if "limit" not in args:
        return None, 0
    try:
        limit = min(int(args["limit"]), MAX_PAGE_SIZE)
        offset = int(args.get("offset", 0))
    except ValueError:
        raise ValidationError("Parâmetros de paginação inválidos")
    return limit, offset
