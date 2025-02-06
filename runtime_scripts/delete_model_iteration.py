
import logging
import argparse
import enum
import datetime
import asyncio
import time
import os
import shutil
import coloredlogs
from openai import timeout
import rcs
from maple_structures.model import ModelIteration
from maple_interface import MapleAPI
from maple_config import config as cfg

ENV = cfg.PRODUCTION

logger = logging.getLogger('ModelIterationDeletion')
logger.info('Starting ModelIterationDeletion script')

TIMEOUT = 120

class DeleteType(enum.Enum):
    all = 'all'
    incomplete = 'incomplete'
    old = 'old'


def delete_model_iteration(delete_type: DeleteType, use_config: bool = True):
    logger.info("Delete model iterations. Deletion type: %s",
                delete_type.value)

    config = cfg.load_config(ENV)

    maple = MapleAPI(
        authority=f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"
    )
    
    if delete_type == DeleteType.old:
        days_limit = int(config['MAPLE_MODEL_ITERATION_DATA_PERSISTENCE_DAYS'])
        logger.debug("Use configuration: %s", use_config)
        if use_config:
            backend_config = maple.config_get()
            logger.debug("Backend configuration: %s", backend_config)
            if isinstance(backend_config, dict):
                if 'model_iteration_persistence_days' in backend_config:
                    days_limit = int(
                        backend_config['model_iteration_persistence_days'])
                else:
                    logger.error(
                        "Backend configuration does not have 'model_iteration_persistence_days'")
                    return
            else:
                logger.error(
                    "Failed to fetch backend configuration. Cancelling deletion.")
                return

        logger.info(
            "Attempt deletion of model iterations older than %d days", days_limit)
        
    model_iterations_reduced = maple.model_iteration_get(reduced=True, timeout=TIMEOUT)
    model_iterations = []
    for model_iteration in model_iterations_reduced:
        if delete_type == DeleteType.old:
            datediff = datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(
                model_iteration.createDate.replace('Z', '+00:00')
            )
            if datediff > datetime.timedelta(days=days_limit):
                model_iteration = maple.model_iteration_get(uuid=model_iteration.uuid, timeout=TIMEOUT)
                if isinstance(model_iteration, list):
                    for model_iteration_ in model_iteration:
                        if isinstance(model_iteration_, ModelIteration):
                            model_iterations.append(model_iteration_)
        else:
            model_iteration = maple.model_iteration_get(uuid=model_iteration.uuid, timeout=TIMEOUT)
            if isinstance(model_iteration, list):
                for model_iteration_ in model_iteration:
                    if isinstance(model_iteration_, ModelIteration):
                        model_iterations.append(model_iteration_)
    logger.debug(
        "Model iterations reduced/fully retrieved: %d/%d", 
        len(model_iterations_reduced), 
        len(model_iterations))
    logger.debug("Model iterations retrieved: %d", len(model_iterations))
    
    delete_model_iterations = []
    for model_iteration in model_iterations:
        if delete_type == DeleteType.old:
            datediff = datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(
                model_iteration.createDate.replace('Z', '+00:00')
            )
            if datediff > datetime.timedelta(days=days_limit):
                delete_model_iterations.append(model_iteration)

        if delete_type == DeleteType.incomplete:
            models = [
                getattr(model_iteration, f'model_level{level}') for level in range(1, 4)]
            complete_models = [True if model.status ==
                               'complete' else False for model in models]
            if not all(complete_models):
                delete_model_iterations.append(model_iteration)

        if delete_type == DeleteType.all:
            delete_model_iterations = model_iterations

    if len(delete_model_iterations) > 0:
        logger.info('Attempt deletion of %d model iterations.',
                    len(delete_model_iterations))
    else:
        logger.info("No model iterations will be deleted.")

    for model_iteration in delete_model_iterations:
        try:
            logger.info('Removing model iteration %s', model_iteration.uuid)
            # remove files associated to model_iteration.
            model_iteration_data_path = os.path.join(
                config['MAPLE_DATA_PATH'],
                config['MAPLE_MODEL_ITERATION_PATH'],
                model_iteration.uuid)
            if os.path.exists(model_iteration_data_path):
                try:
                    logger.debug(
                        'Removing files associated with model iteration %s',
                        model_iteration.uuid)
                    shutil.rmtree(model_iteration_data_path)
                except Exception as exc:
                    logger.error(
                        'Failed to remove directory for model iteration %s. %s',
                        model_iteration.uuid,
                        exc)
                    logger.info(
                        'Model iteration %s will not be deleted.',
                        model_iteration.uuid)
                    continue
            else:
                logger.debug(
                    'Model iteration %s does not have data. Skip data deletion.',
                    model_iteration.uuid)

            if os.path.isfile(f"{model_iteration_data_path}.zip"):
                os.remove(f"{model_iteration_data_path}.zip")

            # remove from backend
            response = maple.model_iteration_delete(model_iteration.uuid, timeout=TIMEOUT)
            if response != 200:
                logger.error(
                    'Failed deletion of model_iteration with uuid: %s. %s',
                    model_iteration.uuid,
                    response)

        except Exception as exc:
            logger.error('Failed to remove model iteration %s.', exc)


async def delete_model_iteration_async(
        delete_type: DeleteType,
        period_seconds: int | None = None,
        use_config: bool = True):

    tstart = time.time()
    while True:
        try:
            delete_model_iteration(
                delete_type=delete_type, use_config=use_config)
            if period_seconds is None:
                wait_time = rcs.utils.time_to_midnight()
            else:
                wait_time = period_seconds - \
                    ((time.time()-tstart) % period_seconds)
                if wait_time < 0:
                    wait_time = 0
                logger.debug("wait_time is %f", wait_time)
            logger.info('Next deletion will occur in %.2f hours',
                        wait_time/60/60)
            await asyncio.sleep(wait_time)
        except Exception as exc:
            logger.error('Failed to remove model iteration. %s', exc)
            await asyncio.sleep(10)

parser = argparse.ArgumentParser()
parser.add_argument(
    '-t',
    nargs='?',
    choices=[e.value for e in DeleteType],
    required=True,
    default=DeleteType.incomplete.value,
    help="The type of deletion to be executed.")
parser.add_argument(
    '-a',
    action='store_true',
    help="Run as asyncio"
)
parser.add_argument(
    '-p',
    type=int,
    help='The period seconds to run the asyncio'
)
parser.add_argument(
    '-l',
    help='The log level',
    default='info',
    choices=['debug', 'info', 'warning', 'error', 'critical'],
)
parser.add_argument(
    '-c',
    '--use_config',
    action='store_true',
    help='''If provided, the configuration will be fetched from backend and used 
    for deletion in case type is old''',
)

if __name__ == '__main__':
    args = parser.parse_args()
    rcs.utils.configure_logging(
        level=args.l,
        output_directory='logs',
        output_filename_prefix='model_iteration_deletion',
        output_file_max_size_bytes=5e6,
        n_log_files=1,
        use_postfix_hour=False,
    )

    coloredlogs.install(level=getattr(logging, args.l.upper()))

    logger.debug('Arguments provided are: %s', args)

    delete_type_ = getattr(DeleteType, args.t)

    if args.a:
        if not args.p:
            logger.info(
                'Period not provided. Deletion will occur every midnight.')
        if delete_type_ != DeleteType.old:
            raise ValueError(
                "In async (a) mode, only 'old' deletion type is accepted.")
        logger.debug("Running script in async mode with period %d.", args.p)
        asyncio.run(
            delete_model_iteration_async(
                delete_type=delete_type_,
                period_seconds=None if not args.p else args.p, 
                use_config=args.use_config)
        )
    else:
        delete_model_iteration(
            delete_type=delete_type_,
            use_config=args.use_config)
