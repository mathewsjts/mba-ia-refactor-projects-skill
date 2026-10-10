"""Relógio UTC sem usar a API deprecated datetime.utcnow() (T12 / AP-19)."""
from datetime import datetime, timezone


def utcnow():
    """UTC atual sem tzinfo, compatível com colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
