import logging
from dotenv import dotenv_values

__logger = logging.getLogger("maple_config")

DEVELOPMENT = ".env.development"
PRODUCTION = ".env.production"
SECRET = ".env.secret"


def load_config(environment: str = None):
    """load configuration file for maple project."""
    config = dotenv_values(DEVELOPMENT)
    try:
        config.update(dotenv_values(SECRET))
    except Exception as exc:
        __logger.error(
            "Could not load secret configuration. Contact admin to request files. %s",
            exc,
        )
    if environment is not None:
        config.update(dotenv_values(environment))
    return config
