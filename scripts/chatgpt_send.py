import logging
import asyncio
import socketio

logger = logging.getLogger('chatgpt send')
logging.basicConfig(level=logging.DEBUG)
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('connection established')

@sio.event
async def disconnect():
    logger.debug('disconnected from server')

async def main():
    await sio.connect('http://localhost:5003')
    for i in range(500):
        try:
            # await sio.emit( 'new_article' , f"uuid___{i}")
            await sio.emit('generate_topic_name',[
            "team",
            "players",
            "league",
            "season",
            "teams",
            "games",
            "hockey",
            "womens",
            "game",
            "head"])
        except Exception as exc:
            logger.error(exc)
        await sio.sleep(1)
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())