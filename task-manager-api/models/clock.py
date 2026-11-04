from datetime import datetime, timezone

from constants import DATE_FORMAT


def utcnow():
    """UTC atual sem tzinfo, compatível com as colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value):
    """Converte 'YYYY-MM-DD' em datetime; devolve None se o valor não estiver nesse formato."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None
