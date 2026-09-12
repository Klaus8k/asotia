from .base import *  # noqa: F403


DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


DATABASES = {
    "default": env.db(  # noqa: F405
        "DATABASE_URL",
        default="postgres://foodshop:foodshop@127.0.0.1:5433/foodshop",
    )
}


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]


MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405


INTERNAL_IPS = [
    "127.0.0.1",
]
