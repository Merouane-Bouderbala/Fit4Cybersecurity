import os

PUBLIC_URL = "cgifit4cybersec"
ALLOWED_HOSTS = ["127.0.0.1", locals().get("PUBLIC_URL", "")]
OPERATOR_EMAIL = "info@example.org"

# The generic site/tool name. Used to load specific config, templates, styles, logo.
SITE_NAME = "fit4cybersecurity"

SECRET_KEY = "b'0I-yjCtk-txeRjtzbyFryEJg0sEYVJ-PlF67-yD-OM0='"

#"-@yli$ylbn5uq4(+kewpfmgnn^b1a-4^h(7=j5p+%__q2v7&(9"
HASH_KEY = "3uMS_te446qSP8QXaOxWf72BFl7a5BcnEphxeNWHRCw=" #generated from Fernet.generate_key()

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fit4cybersecurity",
        "USER": "postgres",
        "PASSWORD": "mynewpassword",
        "HOST": "localhost",
        "PORT": 5432,
    }
}

CORS_ALLOWED_ORIGINS = []
CORS_ALLOWED_ORIGIN_REGEXES = []
CORS_ALLOW_METHODS = [
    "GET",
    "OPTIONS",
]


EMAIL_HOST = "localhost"
EMAIL_PORT = 25

REPORT_TEMPLATE_DIR = "./templates/report/"

# Logging mechanism
LOG_DIRECTORY = "./logs"
LOG_FILE = "django.log"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["file"]},
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIRECTORY, LOG_FILE),
            "formatter": "app",
        },
    },
    "loggers": {
        "django": {"handlers": ["file"], "level": "INFO", "propagate": True},
    },
    "formatters": {
        "app": {
            "format": (
                "%(asctime)s [%(levelname)-8s] (%(module)s.%(funcName)s) %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}
