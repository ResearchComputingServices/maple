
import logging
import argparse
import enum
import datetime
from maple_interface import MapleAPI
from maple_config import config as cfg

ENV = cfg.PRODUCTION

logger = logging.getLogger('ModelIterationDeletion')

config = cfg.load_config(ENV)

class DeleteType(enum.Enum):
    all = 'all'
    incomplete = 'incomplete'
    old = 'old'


def main(delete_type: DeleteType ):
    maple = MapleAPI(
        authority=f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"
    )
    
    model_iterations = maple.model_iteration_get()

    delete_model_iterations = []
    
    for model_iteration in model_iterations:
        if delete_type == DeleteType.old:
            datediff = datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(
                model_iteration.createDate.replace('Z','+00:00')
            )
            if datediff > datetime.timedelta(days=7):
                delete_model_iterations.append(model_iteration)
        
        if delete_type == DeleteType.incomplete:
            models = [getattr(model_iteration,f'model_level{level}') for level in range(1,4)]
            complete_models = [True if model.status == 'complete' else False for model in models]
            if not all(complete_models):
                delete_model_iterations.append(model_iteration)
        
        if delete_type == DeleteType.all:
            delete_model_iterations = model_iterations
    
    
    for model_iteration in delete_model_iterations:
        try:
            logger.info('Removing model iteration %s', model_iteration.uuid)
            response = maple.model_iteration_delete(model_iteration.uuid)
            if response != 200:
                logger.error('Failed deletion of model_iteration with uuid: %s', model_iteration.uuid)

        except Exception as exc:
            logger.error('Failed to remove model iteration %s', s)



parser = argparse.ArgumentParser()
parser.add_argument(
    '-t',
    nargs='?',
    choices=[e.value for e in DeleteType],
    required=True,
    default=DeleteType.incomplete.value,
    help="The type of deletion to be executed.")


if __name__ == '__main__':
    args = parser.parse_args()
    main(delete_type=getattr(DeleteType, args.t))
