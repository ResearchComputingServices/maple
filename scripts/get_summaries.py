import logging
from maple_structures import Article
from maple_interface import MapleAPI
from maple_config import config as cfg 

logger = logging.getLogger('maple_get_summaries')
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

config = cfg.load_config(cfg.PRODUCTION)

maple = MapleAPI(f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}")

summaries = []
urls=[]
LIMIT = 100
total_articles=0
for articles in maple.article_iterator(limit=LIMIT):
    page_count = len(articles)
    total_articles+=page_count
    page_summary_count = 0
    for article in articles:
        if article.url not in urls:
            urls.append(article.url)
        if hasattr(article,'chat_summary'):
            summaries.append(article.chat_summary)
            page_summary_count += 1
    logger.debug('%d/%d articles had summaries',page_summary_count, page_count )
logger.info('Got %d articles, in which %d had chat summaries', total_articles, len(summaries))

logger.info('got %d unique urls', len(urls))  