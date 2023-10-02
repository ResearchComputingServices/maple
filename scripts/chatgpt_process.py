''' recieves a message for every new article. '''
import asyncio
import socketio
import eventlet

from maple_config import config as cfg 

config = cfg.load_config(cfg.DEVELOPMENT)

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    # '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

@sio.event
def connect(sid, environ):
    print('connect', sid, environ)

if __name__ == "__main__":
    eventlet.wsgi.server(
        eventlet.listen(('',int(config['MAPLE_CHAT_PORT']))),
        app)
    

