"""
development.py — local dev settings.

Set in your shell (or .env):
    DJANGO_SETTINGS_MODULE=job_portal.settings.development
"""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# ── SQLite (no setup needed) ───────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── In-memory channels (no Redis needed locally) ───────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ── Print emails to console ────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Disable WhiteNoise compression in dev (faster reload) ──
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
