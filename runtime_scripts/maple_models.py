import logging
import coloredlogs
import argparse
import sys
import rcs
from maple_chatgpt import ChatgptClient
from maple_processing import MapleProcessing, MapleBert
from maple_structures import Article
from maple_interface import MapleAPI
from maple_config import config as cfg


TRAINING_HOURS = 24

parser = argparse.ArgumentParser()
parser.add_argument('--model', nargs='+',
                    choices=['bert', 'lda'], default=['bert'], help='The model to be used')
parser.add_argument('--level', type=str, choices=[
                    'debug', 'info', 'warning', 'error', 'critical'], default='info', help="The log level")
parser.add_argument('-debug-limits', action='store_true', help="Limits the number of articles used in a model iteration. Used for debug purposes.")

logger = logging.getLogger('maple_models')


def main(models, log_level, debug_limits = False):
    ENV = cfg.PRODUCTION
    LOG_OUTPUT_DIRECTORY = 'logs'
    LOG_OUTPUT_FILENAME_PREFIX = 'maple_models'

    coloredlogs.install(level=getattr(logging, log_level.upper()))

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

    config = cfg.load_config(ENV)

    maple = MapleAPI(
        authority=f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}")

    maple_proc = MapleProcessing(
        maple=maple,
        hours=TRAINING_HOURS,
        models=models,
        debug_limits=debug_limits,
    )
    # maple_proc.DEBUG_LIMIT_PROCESS_COUNT = 200
    maple_proc.run(run_once=True)


if __name__ == '__main__':
    args = parser.parse_args()
    logger.debug('Running maple_models with args: %s', args)
    models = []
    if 'bert' in args.model:
        models.append(MapleBert)
    if 'lda' in args.model:
        models.append(MapleLDA)

    main(models, args.level, args.debug_limits)
