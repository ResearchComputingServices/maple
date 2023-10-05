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
from maple_processing.process import chat_summary

# logger = logging.getLogger('MaplePipeline')
# 



class NewsscrapyPipeline:
    '''stores items in the database'''
    logger = logging.getLogger('MaplePipeline')
    # maple = MapleAPI("http://0.0.0.0:3000", apiversion="api/v1")
    _url_history_size = 3000
    _url_history = []
    
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
        
        chatgptkey = None
        if 'MAPLE_CHATGPT35TURBO_APIKEY' in config:
            if config['MAPLE_CHATGPT35TURBO_APIKEY'] != '':
                chatgptkey = config['MAPLE_CHATGPT35TURBO_APIKEY']
        
        return cls(authority, chatgptkey)

    def process_item(self, item, spider):
        self.logger.debug('size of url history is %d', len(self._url_history))
        if 'url' in item:
            if item['url'] not in self._url_history:
                self._url_history.append(item['url'])
                #TODO remove anything older than 24 hours.
                while len(self._url_history) > self._url_history_size:\
                    self._url_history.pop(0)            
                try:
                    self.logger.debug("Attempt sending article to backend")
                    response = self.maple.article_post(Article.from_json(item))
                    if isinstance(response, Article):
                        self.logger.info("New article from %s", response.url)
                        # self.logger.info("Should get chatgpt summary. key %s", self._chatgpt_apikey)
                        #TODO should use chatgpt to summarize
                        # if self._chatgpt_apikey is not None:
                        #     try:
                        #         summary = chat_summary(response.content, self._chatgpt_apikey)
                        #         setattr(response, 'chat_summary', summary)
                        #         response_update = self.maple.article_put(response)
                        #         if isinstance(response_update, Article):
                        #             self.logger.info('chat_summary updated: %s...', response_update.chat_summary[0:80])
                        #     except Exception as exc:
                        #         self.logger.error(exc)
                except Exception as exc:
                    self.logger.error(exc)
                    self._url_history.pop() # remove failed url.
        return item
