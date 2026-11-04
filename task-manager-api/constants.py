"""Valores do domínio, definidos uma vez e importados por validadores, models e services (T16)."""

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_TASK_STATUSES = frozenset({"done", "cancelled"})
DEFAULT_TASK_STATUS = "pending"
DONE_STATUS = "done"

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DUE_DATE_FORMAT = "%Y-%m-%d"

USER_ROLES = ("user", "admin", "manager")
DEFAULT_ROLE = "user"
ADMIN_ROLE = "admin"
PASSWORD_MIN_LENGTH = 4
EMAIL_PATTERN = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"

DEFAULT_CATEGORY_COLOR = "#000000"

RECENT_ACTIVITY_DAYS = 7
MAX_PAGE_SIZE = 100

# Maior inteiro que o SQLite grava; ids acima disso não podem existir.
DB_INTEGER_MAX = 2**63 - 1

EMAIL_TAKEN_MESSAGE = "Email já cadastrado"
USER_NOT_FOUND_MESSAGE = "Usuário não encontrado"
TASK_NOT_FOUND_MESSAGE = "Task não encontrada"
CATEGORY_NOT_FOUND_MESSAGE = "Categoria não encontrada"
