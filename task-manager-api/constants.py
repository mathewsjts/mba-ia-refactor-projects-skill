TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_TASK_STATUSES = ('done', 'cancelled')
DEFAULT_TASK_STATUS = 'pending'

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200

USER_ROLES = ('user', 'admin', 'manager')
ADMIN_ROLE = 'admin'
DEFAULT_ROLE = 'user'
PASSWORD_MIN_LENGTH = 8
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

DEFAULT_CATEGORY_COLOR = '#000000'

DATE_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_DAYS = 7

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Maior inteiro que o SQLite grava; ids acima disso não existem.
MAX_DB_INTEGER = 2 ** 63 - 1
