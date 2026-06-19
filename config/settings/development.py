"""
config/settings/development.py
================================
Development environment settings — DEBUG on, SQLite, verbose errors.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# SQL query logging disabled by default (too verbose).
# Enable by uncommenting the block below:
# LOGGING['loggers']['django.db.backends'] = {  # noqa: F405
#     'handlers': ['console'],
#     'level': 'DEBUG',
#     'propagate': False,
# }

# Django Debug Toolbar (optional — install via requirements-dev.txt)
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Use a faster password hasher in dev (tests run faster)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
