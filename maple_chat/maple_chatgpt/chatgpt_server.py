import logging
import socketio
import asyncio
from threading import Lock
import json
from aiohttp import web
import time
import random
import rcs
from maple_processing.process import LLMProcess, chatgpt_summary, chatgpt_topic_name, chatgpt_bullet_summary
from maple_structures import Article, Topic
from maple_interface import MapleAPI
from .utils import JobType


class ChatgptServerNamespace(socketio.AsyncNamespace):
    logger = logging.getLogger('ChatgptServerNamespace')
    def _verify_chat_key(self, data):
        if 'api_key' in data:
            return True
        self.logger.error('missing chatgpt_key in data')
        return False

    def _verify_content(self, data):
        if 'content' in data:
            return True
        self.logger.error('missing content in data')
        return False

    def on_connect(self, sid, environ, auth = None):
        self.server.client_add(sid)
        # asyncio.ensure_future(self.server.client_add(sid), loop=self.server.loop)

    def on_disconnect(self, sid):
        asyncio.ensure_future(self.server.client_remove(sid))

    async def on_chat_summary(self, sid, data):
        if not self._verify_chat_key(data) or not self._verify_content(data):
            self.logger.error('Received invalid data: %s', data)
            #TODO
        self.logger.debug('on_chat_summary %s %s', sid, data['content'])
        
        self.server.maple_add_job(
            sid = sid,
            api_key = data['api_key'],
            job_type = JobType.summary,
            job_details = data['content']
        )
    
    async def on_get_topic_name(self, sid, data):
        if not self._verify_chat_key(data) or not self._verify_content(data):
            self.logger.error('Received invalid data for topic name')
            #TODO
        self.server.maple_add_job(
            sid = sid,
            api_key = data['api_key'],
            job_type = JobType.topic_name,
            job_details = data['content'],
        )
    
    async def on_get_bullet_summary(self, sid, data):
        if not self._verify_chat_key(data) or not self._verify_content(data):
            self.logger.error('Received invalid data for topic name')
            #TODO
        self.server.maple_add_job(
            sid = sid,
            api_key = data['api_key'],
            job_type = JobType.bullet_summary,
            job_details = data['content']
        )
    
class ChatgptServer(socketio.AsyncServer):
    
    def __init__(
        self,
        maple_api: MapleAPI,
        socket_io_ip: str,
        socket_io_port: int,
        socket_io_api_key: str,
        chatgpt_api_key: str = None,
        article_fetching: bool = False,
        use_config: bool = True) -> None:
        
        super().__init__(ping_timeout=600)
        self.logger=logging.getLogger('ChatgptServer')
        
        self.maple_lock = Lock()
        self.maple_keys_in_use = []
        self.maple_clients = []
        self.maple_jobs = []
        self._maple_config = None
        self._use_config = use_config
        
        self.maple_api = maple_api
        self._socket_io_port = socket_io_port
        self._socket_io_ip =  socket_io_ip
        self._socket_io_api_key = socket_io_api_key
        self._chatgpt_api_key = chatgpt_api_key
        self._article_fetching = article_fetching
        
        self._app = web.Application()
        self.attach(self._app)
        self.register_namespace(ChatgptServerNamespace('/'))
        self.loop = asyncio.get_event_loop()
    
    async def update_config(self):
        FETCH_CONFIG_INTERVAL = 60
        while True:
            if self._use_config:
                max_attempts = 5
                attempts = 0
                while self._maple_config is None and attempts < max_attempts:
                    self.logger.debug("Fetching maple_config")
                    maple_config = self.maple_api.config_get()
                    if maple_config is not None:
                        if self._maple_config != maple_config:
                            self.logger.info('maple_config has changed')
                            self._maple_config = maple_config
                            self.logger.info('Updated maple_config')
                        break
                    attempts +=1
                    await asyncio.sleep(1)
            await asyncio.sleep(FETCH_CONFIG_INTERVAL)
            
        
    def maple_add_job(self, sid: str, api_key: str, job_type: JobType, job_details: any):
        with self.maple_lock:
            job = dict(
                    sid = sid,
                    job_type = job_type,
                    api_key = api_key,
                    job_details = job_details,
                )
            
            if job in self.maple_jobs:
                self.logger.warning("Job was not added! Already exists.")
            else:
                self.maple_jobs.append(
                    job
                )
                self.logger.debug(
                    "Added job: %s. Total jobs: %d", 
                    job_type,
                    len(self.maple_jobs))
    
    async def client_add(self, sid: str):
        """adds a the sid to a list of clients.

        Args:
            sid (str): the session id.
        """
        with self.maple_lock:
            if sid not in self.maple_clients:
                self.maple_clients.append(sid)
                self.logger.debug(
                    'Connected client: %s. List of clients: %s',
                    sid,
                    self.maple_clients)

    async def client_remove(self, sid: str):
        """removes a session id from the list of clients

        Args:
            sid (str): the session id
        """
        with self.maple_lock:
            if sid in self.maple_clients:
                self.maple_clients.remove(sid)
            old_len  = len(self.maple_jobs)
            self.maple_jobs = [job for job in self.maple_jobs if job['sid'] != sid or job['job_type'] in [JobType.summary]]
            self.logger.debug(
                "Removed client (%s) and %d jobs. Current jobs: %d",
                sid,
                old_len-len(self.maple_jobs),
                len(self.maple_jobs)
                )
    
    async def _fetch_pending_summaries(self):
        # await asyncio.sleep(1)
        while True:
            self.logger.info('Fetching articles without chat_summary.')
            try:
                for articles in self.maple_api.article_iterator(limit=1000, page=0):
                    for article in articles:
                        if not hasattr(article, 'chat_summary'):
                            self.maple_add_job(
                                sid=None,
                                api_key = self._chatgpt_api_key,
                                job_type = JobType.summary,
                                job_details = article.to_dict()
                            )
            except Exception as exc:
                self.logger.error('Failed fetch_pending_summaries. %s', exc)
            sec = rcs.utils.time_to_midnight()
            self.logger.info('Next article fetching schedule in %.2f hours.', sec/60/60)
            await asyncio.sleep(sec)

    async def _process_job_summary(self, job, force_update: bool = False):
        # check if uuid in job details
        if 'uuid' not in job['job_details']:
            self.logger.error('Missing uuid for job summary')
            # self.maple_keys_in_use.remove(job['api_key'])
            return
        
        # retrieve article given uuid
        article = None
        for _ in range(5):
            try:
                article = self.maple_api.article_get(uuid=job['job_details']['uuid'])
                
                if isinstance(article, list):
                    if len(article) > 0:
                        article = article[0]
                    else:
                        self.logger.warning('Article with uuid %s does not exist on backend.', job['job_details']['uuid'])
                else:
                    self.logger.warning('Failed retrieving article. %s', article)
                break
            except Exception as exc:
                self.logger.error("Error retrieving article. %s", exc)
                return
        
        # get chat summary using chatgpt
        if isinstance(article, Article):
            # check if already has chat_summary and continue with force_update
            if hasattr(article, 'chat_summary'):
                if not force_update:
                    # self.maple_keys_in_use.remove(job['api_key'])
                    return
            for _ in range(3):
                try:
                    llm_process = LLMProcess(config = self._maple_config)
                    summary = await llm_process.get_summary(article.content, job['api_key'])
                    # summary = await chatgpt_summary(article.content, job['api_key'])
                    # summary = chatgpt_summary(article.content, job['api_key'])
                    break
                except Exception as exc:
                    self.logger.error('Failed to retrieve chat summary using chatgpt. %s', exc)
                    # self.maple_keys_in_use.remove(job['api_key'])
                    return
            
            article.chat_summary = summary
            try:
                self.maple_api.article_put(article)
                self.logger.info('Updated chat_summary for article %s, %s', article.uuid, article.url)
            except Exception as exc:
                self.logger.error('Failed updating article %s. %s', article.uuid, exc)
        # self.maple_keys_in_use.remove(job['api_key'])
    
    async def _process_job_topic_name(self, job):
        job_send = job.copy()
        while True:
            try:
                llm_process = LLMProcess(config = self._maple_config)
                topic_name = await llm_process.get_topic_name(job['job_details']['keyword'], job['api_key'])
                
                # topic_name = await chatgpt_topic_name( job_send['job_details']['keyword'], job_send['api_key'])
                job_send['results'] = topic_name
                break
            except Exception as exc:
                self.logger.error('Failed query from chatgpt. %s', exc)
                return
        
        try:
            if job_send['sid'] is not None:
                self.logger.debug("Sending results of topic name job to %s", job['sid'])
                await self.emit(
                    'topic_name_results',
                    job_send,
                    to=job_send['sid'],
                )
                self.logger.info(
                    "Sent topic name results for topic %s", 
                    job_send['job_details']['uuid'])
        except Exception as exc:
            self.logger.error('Failed replying to job. %s', exc)
    
    async def _process_job_bullet_summary(self, job):
        job_send = job.copy()
        
        while True:
            try:
                articles = job['job_details']['content']
                llm_process = LLMProcess(config = self._maple_config)
                bullet_summary = await llm_process.get_bullet_summary(articles, job['api_key'])
                
                # bullet_summary = await chatgpt_bullet_summary(articles, job['api_key'])
                job_send['results'] = bullet_summary
                break
            except Exception as exc:
                self.logger.error('Failed query from chatgpt: %s', exc)
            
        try:
            if job_send['sid'] is not None:
                self.logger.debug("Sending results of bullet summary job to %s", job['sid'])
                await self.emit(
                    'bullet_summary_results',
                    job_send,
                    to=job_send['sid'],
                )
                self.logger.info(
                    "Sent bullet summary results for topic %s", 
                    job_send['job_details']['uuid'])
        except Exception as exc:
            self.logger.error('Failed replying to job. %s', exc)
        
    async def _process_job(self, job):
        
        self.logger.debug('Processing job: %s, uuid: %s', job['job_type'], job['job_details']['uuid'])
        if job['job_type'] == JobType.summary:
            await self._process_job_summary(job)
            # self.start_background_task(
            #     self._process_job_summary, job
            # )
        
        elif job['job_type'] == JobType.topic_name:
            await self._process_job_topic_name(job)
            # self.maple_keys_in_use.remove(job['api_key'])
        
        elif job['job_type'] == JobType.bullet_summary:
            await self._process_job_bullet_summary(job)
            # self.maple_keys_in_use.remove(job['api_key'])
        
        self.maple_keys_in_use.remove(job['api_key'])
    
    def _get_job(self):
        """get a job to be executed.

        Returns:
            _type_: _description_
        """
        jobs_ = self.maple_jobs.copy()
        # sort by priority (ordered by JobType.all)
        jobs = []
        for job_type in JobType.all:
            for job in jobs_:
                if job['job_type'] == job_type:
                    jobs.append(job)
        
        if len(jobs) != len(jobs_):
            self.logger.warning('There are invalid jobs: (%d)/(%d)', len(jobs_) - len(jobs), len(jobs_))
        
        # return a job if api_key not in use.
        for job in jobs:
            if job['api_key'] not in self.maple_keys_in_use:
                self.maple_keys_in_use.append(job['api_key'])
                self.maple_jobs.remove(job)
                return job
        
        return None
    
    async def _process(self):
        """the process to be executed. run forever...
        """
        tstart = time.time()
        tlog = time.time()
        while True:
            try:
                if (time.time() - tlog) > 5:
                    tlog = time.time()
                    self.logger.debug(
                        'Jobs enqueued: %d. Total time: %.2fh',
                        len(self.maple_jobs),
                        (time.time()-tstart)/60/60,
                        )
                
                job = self._get_job()
                if job is None:
                    await self.sleep(0)
                    continue
                self.start_background_task(self._process_job, job)
                await self.sleep(0)
            except Exception as exc:
                self.logger.error("_process run into problems: %s", exc)
            
        
    def run(self):
        """run server and tasks
        """
        self.start_background_task(self.update_config)
        self.start_background_task(self._process)
        # self.loop.create_task(self._process())
        if self._article_fetching:
            self.start_background_task(self._fetch_pending_summaries)
            # self.loop.create_task(self._fetch_pending_summaries())
        
        web.run_app(
            self._app,
            host = self._socket_io_ip,
            port = self._socket_io_port,
            loop = self.loop,
        )
