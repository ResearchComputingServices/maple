''' recieves a message for every new article. '''

import logging
import rcs
import asyncio
from aiohttp import web
import socketio
import threading 
import time
import argparse
from maple_config import config as cfg 
from maple_interface import MapleAPI
from maple_structures import Article
from maple_processing.process import chat_summary
import os
import sys

LOG_FOLDER = 'logs'
LOG_PREFIX = "chatgpt_process"

parser = argparse.ArgumentParser()

parser.add_argument(
    "-e", choices=["dev", "prod"], default="dev", help="the environment to use"
)
parser.add_argument(
    "-l",
    choices=["debug", "info", "warn", "error", "critical"],
    default="debug",
    help="log level",
)
args= parser.parse_args()

config = cfg.load_config(args.e)
logger = logging.getLogger('chatgpt_process')
        
rcs.utils.configure_logging(
    level=args.l,
    output_directory=LOG_FOLDER,
    output_filename_prefix=LOG_PREFIX)

logging.getLogger('asyncio').setLevel(logging.WARNING)
logger.debug("arguments: %s", args)

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

def update_article(maple, uuid):
    article_updated = True
    articles = maple.article_get(uuid=uuid)
    if len(articles) > 0:
        if len(articles) != 1:
            logger.warning("should not have returned more than one article. uuid: %s, maple: %s", uuid, maple._authority)
        article = articles[0]
        
        if not hasattr(article, 'chat_summary'):
            logger.debug('Attempting chat_summary for article %s', article.uuid)
            # logger.debug(article.to_dict())
            if 'MAPLE_CHATGPT35TURBO_APIKEY' not in config:
                logger.warning('Could not create chat_summary: missing MAPLE_CHATGPT35TURBO_APIKEY')
            else:
                try:
                    _chat_summary = chat_summary(article.content, config['MAPLE_CHATGPT35TURBO_APIKEY'])
                    setattr(article, 'chat_summary', _chat_summary)
                except Exception as exc:
                    logger.error('Failed to set chat_summary. %s', exc)
                    article_updated = False
        
        response = maple.article_put(article)
        if not isinstance(response, Article):
            logger.error('Failed to update article with uuid %s. %s', uuid, response)
            article_updated = False
        elif isinstance(response, Article):
            logger.debug('Successfully updated article with uuid %s', uuid)
    else:
        article_updated = False
        
    return article_updated
                
class ChatProcess:
    _process_uuid = []
    sleep_time_s = 1
    lock = threading.Lock()
    
    def __init__(self) -> None:
        self._maple = MapleAPI(f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}")
        
    
    async def process(self):
        tstart = time.time()
        while True:
            for uiud_i, uuid in enumerate(self._process_uuid.copy()):
                if uiud_i == 0:
                    logger.debug('Processing new batch of uuids')
                logger.debug('Processing uuid %s', uuid)
                if update_article(self._maple, uuid):
                    with self.lock:
                        self._process_uuid.remove(uuid)
                #TODO go over bullet point summaries here...
                
            await asyncio.sleep(self.sleep_time_s)
    
    @property
    def process_uuid(self):
        return self._process_uuid
    
    @process_uuid.setter
    def process_uuid(self, uuid):
        with self.lock:
            self._process_uuid.append(uuid)    


chatprocess = ChatProcess()
loop = asyncio.get_event_loop()
asyncio.ensure_future(chatprocess.process(), loop=loop)


@sio.event
def connect(sid, environ):
    logger.debug('connect %s', sid)
    
@sio.event
def disconnect(sid):
    logger.debug('disconnect %s', sid)
    
@sio.event
async def new_article(sid, data):
    logger.debug('new article: %s, %s', data, sid)
    chatprocess.process_uuid = data
    logger.debug(chatprocess.process_uuid)
    
if __name__ == "__main__":
    chatprocess.sleep_time_s = 1
    web.run_app(
        app,
        host=config['MAPLE_CHAT_IP'],
        port=int(config['MAPLE_CHAT_PORT']),
        loop=loop)
    
    

