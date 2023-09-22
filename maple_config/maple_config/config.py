import logging
from dotenv import dotenv_values

_logger = logging.getLogger("maple_config")

DEVELOPMENT = ".env.development"
PRODUCTION = ".env.production"
SECRET = ".env.secret"


def load_config(environment: str = None):
    """load configuration file for maple project."""
    config = dotenv_values(DEVELOPMENT)
    if environment is not None:
        config.update(dotenv_values(environment))
    try:
        config.update(dotenv_values(SECRET))
        if 'MAPLE_CHATGPT35TURBO_APIKEY' in config:
            _logger.info("chatgpt apikey: %s",config['MAPLE_CHATGPT35TURBO_APIKEY'])
    except Exception as exc:
        _logger.error(
            "Could not load secret configuration. Contact admin to request files. %s",
            exc,
        )
    return config
