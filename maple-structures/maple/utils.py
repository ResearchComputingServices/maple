from datetime import datetime
import logging
logger = logging.getLogger('Maple:Utils')


def get_date_str(value):
    outputformat='%Y%m%d%H%M%S'
    if value is None:
        return ''
    if isinstance(value, str):
        #TODO
        pass
    if isinstance(value, int | float):
        try:
            return datetime.fromtimestamp(value).strftime(outputformat)
        except: 
            try:
                return datetime.fromtimestamp(value/1000).strftime(outputformat)
            except: logger.debug(f"get_date_str:Failed to convert timestamp")
