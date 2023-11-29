from http import client
import logging
import coloredlogs
import asyncio
from uuid import uuid4
import time
import random
from maple_chatgpt import ChatgptClient
# from maple_processing.process import chat_summary
from maple_interface import MapleAPI
from maple_config import config as cfg

logger = logging.getLogger('test_client')
some_keywords = [
    [
        "road",
        "cameras",
        "tickets",
        "city",
        "canada",
        "drive",
        "issued",
        "items",
        "canadian",
        "wps"
    ],
    [
        "new",
        "health",
        "trial",
        "canada",
        "canadian",
        "care",
        "government",
        "legislation",
        "ontario",
        "murder"
    ],
    [
        "holiday",
        "street",
        "community",
        "volunteers",
        "tree",
        "club",
        "library",
        "campaign",
        "barrie",
        "lighting"
    ],
]


def main():
    # logging.basicConfig(level=logging.DEBUG)
    coloredlogs.install(level=logging.DEBUG)
    config = cfg.load_config(cfg.PRODUCTION)
    chatgpt_client = ChatgptClient(
        MapleAPI(
            f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}"),
        # chatgpt_api_key=config['MAPLE_CHATGPT35TURBO_APIKEY'],
        chatgpt_api_key='60cfd06e-06d1-4f4c-8f4e-24e36b543dd7',
        # chatgpt_api_key=str(uuid4()),
        socket_io_api_key=config['MAPLE_CHAT_SOCKETIO_KEY'],
        socket_io_ip=config['MAPLE_CHAT_IP'],
        socket_io_port=5003  # config['MAPLE_CHAT_PORT']
    )
    
    # summary = chat_summary(
    #     "TikTok said Tuesday that operations are underway at the first of its three European data centres, part of the popular Chinese owned app's effort to ease Western fears about privacy risks.\n\r\n\n\r\n\tThe video sharing app said it began transferring European user information to a data centre in Dublin. Two more data centres, another in Ireland and one in Norway, are under construction, TikTok said in an update on its plan to localize European user data, dubbed Project Clover.\n\r\n\n\r\n\t\n\r\n\t\t\nTop science and technology headlines, all in one place\n\r\n\n\r\n\n\r\n\tTikTok has been under scrutiny by European and American regulators over concerns that sensitive user data may end up in China. TikTok is owned by ByteDance, a Chinese company that moved its headquarters to Singapore in 2020.\n\r\n\n\r\n\tTikTok unveiled its plan earlier this year to store data in Europe, where there are stringent privacy laws, after a slew of Western governments banned the app from official devices.\n\r\n\n\r\n\tNCC Group, a British cybersecurity company, is overseeing the project, TikTok's vice president of public policy for Europe, Theo Bertram, said in a blog post.\n\r\n\n\r\n\tNCC Group will check data traffic to make sure that only approved employees \"can access limited data types\" and carry out \"real-time monitoring\" to detect and respond to suspicious access attempts, Bertram said.\n\r\n\n\r\n\t\"All of these controls and operations are designed to ensure that the data of our European users is safeguarded in a specially-designed protective environment, and can only be accessed by approved employees subject to strict independent oversight and verification,",
    #     api_key = config['MAPLE_CHATGPT35TURBO_APIKEY'],
    # )
    

    jobs = []
    # summary jobs
    jobs.extend([dict(
        job_type='summary',
        content=dict(
            uuid=str(uuid4()))) for i in range(10)])
    
    if False:
        # topic name jobs
        for _ in range(10):
            jobs.append(
                dict(
                    job_type='topic_name',
                    content = dict(
                        keyword=some_keywords[random.randint(0,len(some_keywords)-1)],
                        uuid=str(uuid4()),
                        ),
                )
            )
    if True:
        for _ in range(10):
            jobs.append(
                dict(
                    job_type = 'bullet_summary',
                    content = dict(
                        uuid = str(uuid4()),
                        content = [[' '.join(keywords)] for keywords in some_keywords]
                    )
                )
            )
    
    # topic bullet summary
    
    
    count = 0
    
    while True:
        random.shuffle(jobs)
        for job in jobs:
            if job['job_type'] == 'summary':
                chatgpt_client.request_chat_summary(job['content'])
            elif job['job_type'] == 'topic_name':
                chatgpt_client.request_topic_name(job['content'])
            elif job['job_type'] == 'bullet_summary':
                chatgpt_client.request_bullet_summary(job['content'])
            count += 1
            logger.debug(f"{count}: {job['content']}")
            time.sleep(0)
        
        time.sleep(random.randint(60,120))
        chatgpt_client.sleep(0)


if __name__ == "__main__":
    # asyncio.run(main())
    main()
