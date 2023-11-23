import logging
import coloredlogs
from maple_config import config as cfg
from maple_chatgpt import ChatgptServer
from maple_interface import MapleAPI

def main():
    # logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    coloredlogs.install(level=logging.DEBUG)
    config = cfg.load_config(cfg.PRODUCTION)
    server = ChatgptServer(
        MapleAPI(f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"),
        chatgpt_api_key=config['MAPLE_CHATGPT35TURBO_APIKEY'],
        socket_io_ip = config['MAPLE_CHAT_IP'],
        socket_io_port = 5004,# config['MAPLE_CHAT_PORT'],
        socket_io_api_key = config['MAPLE_CHAT_SOCKETIO_KEY'],
        # article_fetching=True,
    )
    server.run()

if __name__ == "__main__":
    main()