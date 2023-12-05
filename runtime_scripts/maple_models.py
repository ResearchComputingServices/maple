import logging
import coloredlogs
import argparse
import os
import rcs
from maple_chatgpt import ChatgptClient, chatgpt_client
from maple_processing import MapleProcessing, MapleBert, MapleModel
from maple_structures import Article
from maple_interface import MapleAPI
from maple_config import config as cfg


TRAINING_HOURS = 24

parser = argparse.ArgumentParser()
parser.add_argument('--model', nargs='+',
                    choices=['bert', 'lda'], default=['bert'], help='The model to be used')
parser.add_argument('--level', type=str, choices=[
                    'debug', 'info', 'warning', 'error', 'critical'], default='info', help="The log level")
parser.add_argument('--debug-limits', action='store_true', help="Limits the number of articles used in a model iteration. Used for debug purposes.")
parser.add_argument('--run-once', action='store_true',help="If provided, model_iteration will be executed only once.")
logger = logging.getLogger('maple_models')


def main(*,
    models: list[MapleModel],
    log_level: str,
    debug_limits: bool = False,
    run_once: bool = False
    ):
    ENV = cfg.PRODUCTION
    LOG_OUTPUT_DIRECTORY = 'logs'
    LOG_OUTPUT_FILENAME_PREFIX = 'maple_models'

    
    # Reduce log messages of some packages.
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    rcs.utils.configure_logging(
        level=log_level,
        output_to_console=False,
        output_directory=LOG_OUTPUT_DIRECTORY,
        output_filename_prefix=LOG_OUTPUT_FILENAME_PREFIX,
        n_log_files=3,
        use_postfix_hour=False,
        force=True
    )
    
    coloredlogs.install(level=getattr(logging, log_level.upper()))

    config = cfg.load_config(ENV)

    maple = MapleAPI(
        authority=f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}")

    chatgpt_client = ChatgptClient(
        maple,
        chatgpt_api_key=config['MAPLE_CHATGPT35TURBO_APIKEY'],
        socket_io_api_key=config['MAPLE_CHAT_SOCKETIO_KEY'],
        socket_io_ip=config['MAPLE_CHAT_IP'],
        socket_io_port=config['MAPLE_CHAT_PORT'],
        connection_required=True,
        )
    
    maple_proc = MapleProcessing(
        maple=maple,
        hours=TRAINING_HOURS,
        models=models,
        debug_limits=debug_limits,
        chatgpt_client=chatgpt_client,
        model_iteration_datapath=os.path.join(
            config['MAPLE_DATA_PATH'],
            config['MAPLE_MODEL_ITERATION_PATH'],
        ),
    )

    # maple_proc.DEBUG_LIMIT_PROCESS_COUNT = 200
    maple_proc.run(run_once=run_once)


if __name__ == '__main__':
    args = parser.parse_args()
    logger.debug('Running maple_models with args: %s', args)
    models = []
    if 'bert' in args.model:
        models.append(MapleBert)
    if 'lda' in args.model:
        models.append(MapleLDA)

    main(
        models=models,
        log_level=args.level,
        debug_limits=args.debug_limits,
        run_once=args.run_once)
