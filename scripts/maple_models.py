import logging
from maple_processing import MapleProcessing, MapleBert
from maple_interface import MapleAPI

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.INFO)

    TRAINING_HOURS = 24
    maple = MapleAPI(authority='http://134.117.214.192:80')
    maple_proc = MapleProcessing(
        maple=maple,
        hours=TRAINING_HOURS,
        models=[
            # MapleModel,
            MapleBert,
            # MapleLDA,
        ],
        # debug_limits=True,
    )
    # maple_proc.DEBUG_LIMIT_PROCESS_COUNT = 200
    maple_proc.run(run_once=True)
