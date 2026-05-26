from .base import *


DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://foodshop:foodshop@127.0.0.1:5432/foodshop",
    )
}


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


INSTALLED_APPS += [
    "debug_toolbar",
]


MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE


INTERNAL_IPS = [
    "127.0.0.1",
]