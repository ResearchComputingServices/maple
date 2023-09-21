# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
from itemadapter import ItemAdapter
from maple_interface import MapleAPI
from maple_structures import Article
from maple_config import config as cfg

# logger = logging.getLogger('MaplePipeline')
# 

class NewsscrapyPipeline:
    '''stores items in the database'''
    logger = logging.getLogger('MaplePipeline')
    # maple = MapleAPI("http://0.0.0.0:3000", apiversion="api/v1")
    
    def __init__(self, authority, chatgpt_apikey = None) -> None:
        self.maple = MapleAPI(authority, apiversion='api/v1')
        self._chatgpt_apikey = chatgpt_apikey
        
    @classmethod
    def from_crawler(cls, crawler):
        _settings = crawler.settings
        cls.logger.info("Environment: %s",_settings['MAPLE_ENVIRONMENT'])
        config = cfg.load_config(_settings['MAPLE_ENVIRONMENT'])
        authority = "http://0.0.0.0:3000"
        if 'MAPLE_BACKEND_IP' in config and 'MAPLE_BACKEND_PORT' in config:
            authority = f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"
        cls.logger.debug("Using authority: %s", authority)
        return cls(authority)

    def process_item(self, item, spider):
        try:
            response = self.maple.article_post(Article.from_json(item))
            if isinstance(response, Article):
                self.logger.info("New article from %s", response.url)
                self.logger.info("Should get chatgpt summary. key %s", self._chatgpt_apikey)
                #TODO should use chatgpt to summarize
        except Exception as exc:
            self.logger.error(exc)
        return item
