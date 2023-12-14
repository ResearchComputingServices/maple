# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
import requests
import time
from itemadapter import ItemAdapter
import bcrypt
from maple_interface import MapleAPI
from maple_structures import Article
from maple_config import config as cfg
from maple_chatgpt import ChatgptClient
# from maple_processing.process import chatgpt_summary

import socketio
from socketio import exceptions
import threading

config = cfg.load_config(cfg.DEVELOPMENT)

class ProcessArticles:
    uuids_to_process = []
    name = 'ProcessArticles'
    
    def __init__(self) -> None:
        global config
        self.chatgpt_client = ChatgptClient(
            MapleAPI(
            f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"),
            chatgpt_api_key=config['MAPLE_CHATGPT35TURBO_APIKEY'],
            socket_io_api_key=config['MAPLE_CHAT_SOCKETIO_KEY'],
            socket_io_ip=config['MAPLE_CHAT_IP'],
            socket_io_port=config['MAPLE_CHAT_PORT'],
            connection_required = False,
        )
        # self.sio = socketio.Client()
        self.logger = logging.getLogger(self.name)
        
    def add_uuid(self, uuid):
        if uuid not in self.uuids_to_process:
            self.uuids_to_process.append(uuid)
        self.logger.debug("uuids to process: %s", self.uuids_to_process)
    
    def send_uuids(self):
        
        uuids = self.uuids_to_process.copy()
    
        for uuid in uuids:
            try:
                self.logger.debug('sending chat_summary request with uuid %s', uuid)
                self.chatgpt_client.request_chat_summary({'uuid': uuid}, until_success=False)
                self.uuids_to_process.remove(uuid)
                self.logger.debug('request with uuid %s sent!', uuid)
            except Exception as exc:
                self.logger.error('Failed to send uuid %s. Retry on next call.', uuid, exc)        
    
class NewsscrapyPipeline:
    '''stores items in the database'''
    logger = logging.getLogger('MaplePipeline')
    # maple = MapleAPI("http://0.0.0.0:3000", apiversion="api/v1")
    _url_history_size = 3000
    _url_history = []
    _process_articles = ProcessArticles()
    
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
                self._url_history.append((item['url'], time.time()))
                #remove anything older than 24 hours.
                while True:
                    if len(self._url_history) > 0:
                        if (time.time() - self._url_history[0][1]) > 86400:
                            self.logger.debug('removing article from url history: %s', self._url_history[0][1]['url'])
                            self._url_history.pop(0)
                        else:
                            break
                    else:
                        break
                # Limit the number of urls in url history
                while len(self._url_history) > self._url_history_size:\
                    self._url_history.pop(0)            
                try:
                    self.logger.debug("Attempt sending article to backend")
                    response = self.maple.article_post(Article.from_json(item))
                    if isinstance(response, Article):
                        self.logger.info("New article (%s) from %s", response.uuid, response.url)
                        self._process_articles.add_uuid(response.uuid)
                        self._process_articles.send_uuids()
                    elif isinstance(response, requests.Response):
                        if response.status_code == 400:
                            self.logger.debug('Article already exist in backend: %s', item['url'] if 'url' in item else 'unknown url')
                        else:
                            self.logger.warning('Could not store article. Status code: %d, %s', response.status_code, response.text)
                except Exception as exc:
                    self.logger.error(exc)
                    self._url_history.pop() # remove failed url.
        return item
