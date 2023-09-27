

import logging
from maple_structures import Article
from maple_interface import MapleAPI
from maple_processing.process import chat_summary
from maple_config import config as cfg


logger = logging.getLogger("random_test")
logging.basicConfig(level=logging.DEBUG)

maple = MapleAPI('http://0.0.0.0:3000')

config = cfg.load_config(cfg.DEVELOPMENT)
logger.debug("Configuration loaded: %s", config)

if "MAPLE_CHATGPT35TURBO_APIKEY" not in config:
    raise KeyError("could not load MAPLE_CHATGPT35TURBO_APIKEY")

articles = maple.article_get(limit=1)
if len(articles) == 0:
    raise RuntimeError('failed to fetch article')

article = articles[0]
logger.debug("content: %s", article.content)
ret = chat_summary(article.content, config['MAPLE_CHATGPT35TURBO_APIKEY'])

pass

