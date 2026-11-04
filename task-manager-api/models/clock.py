from datetime import datetime, timezone


def utcnow():
    """UTC atual sem tzinfo, compatível com as colunas DateTime sem timezone (T12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
