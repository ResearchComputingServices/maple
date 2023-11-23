import logging
import socketio
from socketio.exceptions import BadNamespaceError, ConnectionError
import threading
import asyncio
from uuid import uuid4
from maple_structures import Article, Topic
from maple_interface import MapleAPI
from .utils import JobType

logger = logging.getLogger('chatgpt_client')
sio = socketio.AsyncClient()

class ChatgptClient(socketio.AsyncClientNamespace):
    _sio = sio
    
    def __init__(
        self,
        maple_api: MapleAPI,
        chatgpt_api_key: str,
        socket_io_api_key: str,
        socket_io_ip: str,
        socket_io_port: int) -> None:
        """Chatgpt Client connects to socketio server to request chatgpt operations

        Args:
            maple_api (MapleAPI): the maple_api for connections with backend server.
            chatgpt_api_key (str): the api_key required by open_ai to do requests.
        """
        self.maple_api = maple_api
        self._chatgpt_api_key =  chatgpt_api_key
        self._socket_io_api_key = socket_io_api_key
        self._socket_io_ip = socket_io_ip
        self._socket_io_port = socket_io_port
        self._loop = asyncio.get_event_loop()
        self._loop.run_until_complete(self._connect())
    
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass
    
    async def _connect(self):
        while True:
            try:
                await self._sio.connect(
                    f'http://{self._socket_io_ip}:{self._socket_io_port}',
                    dict(API_KEY = self._socket_io_api_key),
                )
                break
            except ConnectionError:
                logger.debug('Failed connection to server.')
                await asyncio.sleep(1)
                continue
    
    # async def connect_to_server(self, ip: str, port: int, api_key: str):
    #     await self._sio.connect(f'http://{ip}:{port}', auth=dict(API_KEY = api_key))
    
    def request_chat_summary(self, article: dict, until_success: bool = True):
        if self._sio.connected:
            while True:
                try:
                    self._loop.run_until_complete(
                        self._sio.emit(
                            'chat_summary', 
                            dict(
                                api_key = self._chatgpt_api_key,
                                content = article,
                            )
                        )
                    )
                    break
                except BadNamespaceError as exc:
                    logger.debug('Failed to send chat summary %s', exc)
                    if not until_success:
                        logger.debug("Canceling chat summary")
                        return
                    self._loop.run_until_complete(asyncio.sleep(1))
    
    def request_topic_name(self, topic: dict, until_success: bool = True):
        required_keys = ['uuid', 'keyword']
        for key in required_keys:
            if key not in topic:
                raise ValueError('missing required key for topic name: %s', key)
        if self._sio.connected:
            while True:
                try:
                    self._loop.run_until_complete(
                        self._sio.emit(
                            'get_topic_name',
                            dict(
                                api_key = self._chatgpt_api_key,
                                content = topic,
                            )
                        )
                    )
                    break
                except BadNamespaceError as exc:
                    if not until_success:
                        raise exc
                    continue
        else:
            raise ConnectionError('socketio not connected.')

    def request_bullet_summary(self, topic: dict, until_success: bool = True):
        required_keys = ['uuid', 'content']
        for key in required_keys:
            if key not in topic:
                raise ValueError(f"Missing key for bullet summary: {key}")
        while True:
            try:
                self._loop.run_until_complete(
                    self._sio.emit(
                        'get_bullet_summary',
                        dict(
                            api_key = self._chatgpt_api_key,
                            content = topic,
                        )
                    )
                )
                break
            except BadNamespaceError as exc:
                if not until_success:
                    raise exc
                continue