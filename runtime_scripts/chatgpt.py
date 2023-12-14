import logging
import coloredlogs
import rcs
from maple_config import config as cfg
from maple_chatgpt import ChatgptServer
from maple_interface import MapleAPI

LOG_LEVEL = 'debug'
LOG_OUTPUT_DIRECTORY = 'logs'
LOG_OUTPUT_FILENAME_PREFIX = 'chatgpt'

rcs.utils.configure_logging(
    level=LOG_LEVEL,
    output_to_console=False,
    output_directory=LOG_OUTPUT_DIRECTORY,
    output_filename_prefix=LOG_OUTPUT_FILENAME_PREFIX,
    n_log_files=3,
    use_postfix_hour=False,
    force=True
)

coloredlogs.install(level=getattr(logging, LOG_LEVEL.upper()))

# Reduce log messages of some packages.
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


config = cfg.load_config(cfg.PRODUCTION)

server = ChatgptServer(
    MapleAPI(
        f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"),
    chatgpt_api_key=config['MAPLE_CHATGPT35TURBO_APIKEY'],
    socket_io_ip=config['MAPLE_CHAT_IP'],
    socket_io_port=config['MAPLE_CHAT_PORT'],
    socket_io_api_key=config['MAPLE_CHAT_SOCKETIO_KEY'],
    article_fetching=True,
)

server.run()
