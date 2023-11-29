import logging
from numpy import require
import socketio
from socketio.exceptions import BadNamespaceError, ConnectionError
import threading
import asyncio
from uuid import uuid4
from maple_structures import Article, Topic
from maple_interface import MapleAPI
from .utils import JobType

logger = logging.getLogger('chatgpt_client')



class ChatgptClientNamespace(socketio.ClientNamespace):
    def on_connect(self):
        self.client.logger.debug('on_connect')

    def on_disconnect(self):
        self.client.logger.debug('on_disconnect')

    def on_topic_name_results(self, data):
        self.client.logger.debug(data)
        self.client.topic_name_results.append(data)
    
    def on_bullet_summary_results(self, data):
        self.client.topic_bullet_summary_results.append(data)
        self.client.logger.debug(
            "Received bullet summary for topic (%d). %s",
            len(self.client.topic_bullet_summary_results),
            data['job_details']['uuid'])
        pass


class ChatgptClient(socketio.Client):
    def __init__(
        self,
        maple_api: MapleAPI,
        chatgpt_api_key: str,
        socket_io_api_key: str,
        socket_io_ip: str,
        socket_io_port: int,
        connection_required: bool = True) -> None:
        """Chatgpt Client connects to socketio server to request chatgpt operations

        Args:
            maple_api (MapleAPI): the maple_api for connections with backend server.
            chatgpt_api_key (str): the api_key required by open_ai to do requests.
        """
        super().__init__()
        self.logger = logging.getLogger('ChatgptClient')
        self.maple_api = maple_api
        self._chatgpt_api_key =  chatgpt_api_key
        self._socket_io_api_key = socket_io_api_key
        self._socket_io_ip = socket_io_ip
        self._socket_io_port = socket_io_port
        self._connection_required = connection_required
        
        self.topic_name_results = []
        self.topic_bullet_summary_results = []
        self.register_namespace(ChatgptClientNamespace('/'))
        self._connect()

    def on_connect(self):
        print('on_connect')
        pass


    def on_disconnect(self):
        print('on_disconnect')
        pass

    def _connect(self):
        while True:
            try:
                self.connect(
                    f'http://{self._socket_io_ip}:{self._socket_io_port}',
                    dict(API_KEY = self._socket_io_api_key),
                )
                break
            except ConnectionError as exc:
                self.logger.error('Could not connect to server. %s', exc)
                self.sleep(1)
                if not self._connection_required:
                    return

    def request_chat_summary(self, article: dict, until_success: bool = True):
        required_keys=['uuid']
        for key in required_keys:
            if key not in article:
                raise ValueError('missing required key for article: %s', key)
        
        if not self.connected:
            self._connect()
            
        while True:
            try:
                self.emit(
                    'chat_summary', 
                    dict(
                        api_key = self._chatgpt_api_key,
                        content = article,
                    )
                )
                break
            except BadNamespaceError as exc:
                self.logger.warning("Attempted sending request for chat summary, but failed. Reattempting... %s", exc)
                if until_success:
                    self.logger.warning(
                        "Reattempt sending request for chat summary with uuid %s... %s",
                        article['uuid'],
                        exc)
                    self.sleep(1)
                    continue
                raise exc
            

    def request_topic_name(self, topic: dict, until_success: bool = True):
        required_keys = ['uuid', 'keyword']
        for key in required_keys:
            if key not in topic:
                raise ValueError('missing required key for topic name: %s', key)
        
        if not self.connected:
            self._connect()
        
        while True:
            try:
                self.emit(
                    'get_topic_name',
                    dict(
                        api_key = self._chatgpt_api_key,
                        content = topic,
                    ),
                    )
                break
            except BadNamespaceError as exc:
                if until_success:
                    self.logger.warning("Attempted sending request for topic name, but failed. Reattempting... %s", exc)
                    self.sleep(1)
                    continue
                raise exc
        

    def request_bullet_summary(self, topic: dict, until_success: bool = True):
        required_keys = ['uuid', 'content']
        for key in required_keys:
            if key not in topic:
                raise ValueError(f"Missing key for bullet summary: {key}")
        
        if not self.connected:
            self._connect()
            
        while True:
            try:
                self.emit(
                    'get_bullet_summary',
                    dict(
                        api_key = self._chatgpt_api_key,
                        content = topic,
                    )
                )
                break
            except BadNamespaceError as exc:
                if until_success:
                    self.logger.warning("Attempted sending request for bullet summary, but failed. Reattempting... %s", exc)
                    self.sleep(1)
                    continue
                raise exc
