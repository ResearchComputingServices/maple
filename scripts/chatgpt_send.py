import logging
import asyncio
import socketio
import bcrypt
from uuid import uuid4
from maple_config import config as cfg

config=cfg.load_config(cfg.DEVELOPMENT)

logger = logging.getLogger('chatgpt send')
logging.basicConfig(level=logging.DEBUG)
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('connection established')

@sio.event
async def disconnect():
    logger.debug('disconnected from server')

@sio.event
async def generated_topic_name(data):
    logger.debug('Generated topic name is %s', data)

def printoutret(*args):
    logger.debug(args)

async def main():
    await sio.connect(
        'http://0.0.0.0:5003', 
        auth=dict(API_KEY= bcrypt.hashpw(
            config['MAPLE_CHAT_SOCKETIO_KEY'].encode(), 
            bcrypt.gensalt()).decode()))
    for i in range(500):
        try:
            # await sio.emit( 'new_article' , f"uuid___{i}")
            await sio.emit(
                'generate_topic_name',
                str(uuid4()),
                [
                    "team",
                    "players",
                    "league",
                    "season",
                    "teams",
                    "games",
                    "hockey",
                    "womens",
                    "game",
                    "head"],
                callback=printoutret)
            
        except Exception as exc:
            logger.error(exc)
        await sio.sleep(5)
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())