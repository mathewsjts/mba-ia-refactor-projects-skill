"""Constantes de domínio centralizadas (enums e limites)."""

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_STATUSES = frozenset({"done", "cancelled"})
USER_ROLES = ("user", "admin", "manager")

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = "#000000"

EMAIL_REGEX = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
