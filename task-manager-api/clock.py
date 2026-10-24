"""Relógio UTC compatível com colunas DateTime sem timezone (substitui datetime.utcnow)."""
from datetime import datetime, timezone


def utcnow():
    """UTC atual sem tzinfo, preservando o formato de texto das respostas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
