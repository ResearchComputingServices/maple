''' recieves a message for every new article. '''
import asyncio
import socketio
import eventlet
import logging
from maple_config import config as cfg 

config = cfg.load_config(cfg.DEVELOPMENT)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    # '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

class ChatProcess:
    to_process = []
    
    def process(self):
        for uuid in self.to_process:
            logger.debug('Processing uuid %s', uuid)
            self.to_process.remove(uuid)
            

chatprocess = ChatProcess()

@sio.event
def connect(sid, environ):
    print('connect', sid, environ)

@sio.event
def new_article(data, tst):
    print('new article: %s, %s', data, tst)
    chatprocess.to_process.append(data)
    chatprocess.process()
    
# async def test():
#     a = 0 
#     while True:
#         a +=1
#         print(a)
#         await asyncio.sleep(1)

# async def test_server():
#     await eventlet.wsgi.server(
#         eventlet.listen(('',int(config['MAPLE_CHAT_PORT']))),
#         app)
    
# async def _main():
#     await asyncio.gather(
#         test(),
#         test_server())
    
if __name__ == "__main__":
    # asyncio.run(_main())
    
    eventlet.wsgi.server(
        eventlet.listen(('',int(config['MAPLE_CHAT_PORT']))),
        app)
    
    

