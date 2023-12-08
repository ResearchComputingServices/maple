''' recieves a message for every new article. '''

import logging
import rcs
import asyncio
from aiohttp import web
import requests
import socketio
import threading 
import time
import argparse
import bcrypt
from maple_config import config as cfg 
from maple_interface import MapleAPI
from maple_structures import Article
from maple_processing.process import chatgpt_summary, chatgpt_topic_name, chatgpt_bullet_summary
from uuid import uuid4
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
MAPLE_CHAT_SOCKETIO_KEY = config['MAPLE_CHAT_SOCKETIO_KEY'].encode() if 'MAPLE_CHAT_SOCKETIO_KEY' in config else None
MAPLE_CHATGPT_KEY = config['MAPLE_CHATGPT35TURBO_APIKEY'] if 'MAPLE_CHATGPT35TURBO_APIKEY' in config else None
logger = logging.getLogger('chatgpt_process')

clients = []
        
rcs.utils.configure_logging(
    level=args.l,
    output_directory=LOG_FOLDER,
    output_filename_prefix=LOG_PREFIX,
    output_file_max_size_bytes=5e6,
    n_log_files = 4,
    use_postfix_hour = False)

logging.getLogger('asyncio').setLevel(logging.WARNING)
logger.debug("arguments: %s", args)

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

def update_article(maple, uuid):
    article_updated = True
    articles = maple.article_get(uuid=uuid)
    if isinstance(articles, requests.Response):
        logger.error('Failed to retrieve article')
        logger.debug('Response %d %s', articles.status_code, articles)
        return False
    if len(articles) > 0:
        if len(articles) != 1:
            logger.warning("should not have returned more than one article. uuid: %s, maple: %s, len %d", uuid, maple._authority, len(articles))
        article = articles[0]
        
        if not hasattr(article, 'chat_summary'):
            logger.debug('Attempting chat_summary for article %s', article.uuid)
            # logger.debug(article.to_dict())
            if not MAPLE_CHATGPT_KEY:
                logger.warning('Could not create chat_summary: missing MAPLE_CHATGPT35TURBO_APIKEY')
            else:
                try:
                    _chat_summary = chatgpt_summary(article.content, MAPLE_CHATGPT_KEY)
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
    _process_generate_topic_name = []
    sleep_time_s = 1
    lock = threading.Lock()

    def __init__(self) -> None:
        self._maple = MapleAPI(f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}")
        # self.__get_unprocessed_uuids()
    
    def generate_topic_name(self, uuid: str, keywords: list[str], sid: str):
        topic_name_job = dict(
            sid = sid,
            uuid = uuid,
            keywords = keywords.copy()
        )
        with self.lock:
            self._process_generate_topic_name.append(
                topic_name_job
            )
        return topic_name_job['uuid']
    
    async def _process_topic_names(self):
        global clients
        with self.lock:
            topic_name_jobs = self._process_generate_topic_name.copy()
        
        for topic_name_job in topic_name_jobs:
            logger.debug('Processing topic name job %s', topic_name_job)
            # if client is not connected, remove jobs
            if topic_name_job['sid'] not in clients:
                logger.warning(
                    'will not update topic_name for sid %s as it is not connected',
                    topic_name_job['sid'])
                with self.lock:
                    if topic_name_job in self._process_generate_topic_name:
                        self._process_generate_topic_name.remove(topic_name_job)
                continue
            
            try:
                if not MAPLE_CHATGPT_KEY:
                    logger.warning('Could not generate topic name as the chatgpt key is not available.')
                    continue
                
                #TODO
                # topic_name = chatgpt_topic_name(topic_name_job['keywords'], MAPLE_CHATGPT_KEY)
                topic_name = await asyncio.sleep(8)
                topic_name = 'Topic name test.'
                
                topic_name_job['topic_name'] = topic_name
                await sio.emit(
                    'generated_topic_name', 
                    topic_name_job,
                    to=topic_name_job['sid'])
                with self.lock:
                    try:
                        for job in self._process_generate_topic_name.copy():
                            if job['uuid'] == topic_name_job['uuid']:
                                self._process_generate_topic_name.remove(job)
                    except ValueError as exc:
                        logger.error('Failed to remove topic name job. %s. %s ', topic_name_job, exc)
            except:
                logger.error('Failed to send topic name')
                
    async def higher_priority_tasks(self):
        # logger.debug('Running higher priority tasks...')
        #TODO generate dot summary for top n articles
        
        await self._process_topic_names()
            
    
    async def get_unprocessed_uuids(self):
        """ Retrieves all unprocessed uuids for later processing.
        """
        while True:
            logger.info('Retrieving unprocessed uuids')
            try:
                for articles in self._maple.article_iterator(limit=1000):
                    for article in articles:
                        if not hasattr(article, 'chat_summary'):
                            with self.lock:
                                self._process_uuid.append(article.uuid)
            except Exception as exc:
                logger.error('Failed to get unprocessed article uuids. %s', exc)
                
            sec = rcs.utils.time_to_midnight()
            logger.info('retrieving of uuids will be performed again in %f hours.', sec/60/60)
            await asyncio.sleep(sec)
            
    async def process(self):
        tstart = time.time()
        debug_time = tstart
        loop_ = asyncio.get_event_loop()
        while True:
            
            # First run all higher priority tasks
            await self.higher_priority_tasks()
            
            if ((time.time() - debug_time) >= 60):
                debug_time = time.time()
                logger.debug('elapsed time: (%d)', time.time()-tstart)
            batch_of_uuids = self._process_uuid.copy()
            for uuid_i, uuid in enumerate(batch_of_uuids):
                # First run all higher priority tasks
                await self.higher_priority_tasks()
                
                if uuid_i == 0:
                    logger.debug('Processing new batch of uuids (%d)', len(batch_of_uuids))
                logger.debug('Processing uuid %s (%d/%d)', uuid, uuid_i+1, len(batch_of_uuids))
                
                updated_article = await loop_.run_in_executor(None, update_article, self._maple, uuid)
                if updated_article:
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
asyncio.ensure_future(chatprocess.get_unprocessed_uuids(), loop=loop)


@sio.event
def connect(sid, environ, auth: dict = None):
    logger.debug('connect %s', sid)
    global MAPLE_CHAT_SOCKETIO_KEY
    global clients
    
    if MAPLE_CHAT_SOCKETIO_KEY:
        if not 'API_KEY' in auth:
            return False
        try:
            if bcrypt.checkpw(MAPLE_CHAT_SOCKETIO_KEY, auth['API_KEY'].encode()):
                clients.append(sid)
                logger.debug('Client %s included to list of clients.\nClients: %s', sid, clients)
                return
            else:
                return False
        except:
            return False
    return False

   
@sio.event
def disconnect(sid):
    logger.debug('disconnect %s', sid)
    global clients
    if sid in clients:
        clients.remove(sid)
    # TODO remove all jobs related to this sid
    
@sio.event
async def new_article(sid, data):
    logger.debug('new article: %s, %s', data, sid)
    chatprocess.process_uuid = data
    logger.debug(chatprocess.process_uuid)

@sio.event
async def generate_topic_name(sid, uuid: str, keywords: list[str]):
    logger.debug('%s', keywords)
    return chatprocess.generate_topic_name(uuid, keywords, sid=sid)
    
    
if __name__ == "__main__":
    chatprocess.sleep_time_s = 1
    web.run_app(
        app,
        host=config['MAPLE_CHAT_IP'],
        port=int(config['MAPLE_CHAT_PORT']),
        loop=loop)
    
    

