"""
production.py — Railway / Render / any PaaS.

Required environment variables (set in platform dashboard):
    SECRET_KEY
    DATABASE_URL
    ALLOWED_HOSTS
    DJANGO_SETTINGS_MODULE=job_portal.settings.production

Optional:
    REDIS_URL            (defaults to redis://localhost:6379)
    EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD
    DEFAULT_FROM_EMAIL
"""
from .base import *  # noqa: F401, F403
import dj_database_url
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# ── Database ───────────────────────────────────────────────
# Railway / Render inject DATABASE_URL automatically.
# ssl_require=False here because the URL already contains ?sslmode=require
# when the platform sets it — setting it to True again causes a conflict.
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=False,
    )
}

# ── Redis / Channels ───────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL', default='redis://localhost:6379')],
        },
    }
}

# ── Email ──────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = config('EMAIL_HOST',     default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',     default=587, cast=int)
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='noreply@HireHub.com')

# ── HTTPS / Security headers ───────────────────────────────
# Railway and Render terminate SSL at the proxy layer and forward
# HTTP internally — SECURE_PROXY_SSL_HEADER tells Django to trust
# the X-Forwarded-Proto header the proxy sets.
SECURE_PROXY_SSL_HEADER       = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT           = True
SESSION_COOKIE_SECURE         = True
CSRF_COOKIE_SECURE            = True
SECURE_HSTS_SECONDS           = 31_536_000   # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD           = True
SECURE_CONTENT_TYPE_NOSNIFF   = True
X_FRAME_OPTIONS               = 'DENY'
