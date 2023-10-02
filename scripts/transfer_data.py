'''transfer data from one db to another'''
import logging
import argparse
import requests
import json
from pprint import pprint as p
from maple_structures import Article
from maple_interface import MapleAPI

logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("maple_transfer")

parser = argparse.ArgumentParser()
parser.add_argument('-s', type= str,required=True, help='the source ip and port. e.g. 0.0.0.0:3000')
parser.add_argument('-d', type= str,required=True, help='the source ip and port. e.g. 0.0.0.0:3000')
parser.add_argument('-n', type=int, required=False, default=None, help='the number of articles to transfer. If not provided, all will be transfered.')
parser.add_argument('-j', type= int, required= False, default=0, help='how many articles to skip')


def print_summary(transferred, attempted):
    logger.info(f"Summary:\ntransferred {transferred}/{attempted} articles.")

def transfer(maples: MapleAPI, mapled: MapleAPI, n: int, skip: int):
    '''transfer articles from one backend to another'''
    transferred = 0
    attempted = 0
    while True:
        for articles in maples.article_iterator(limit=1, page=attempted+skip):
            if len(articles) == 0:
                return
            for article in articles:
                
                update_author = False
                if '_author' in article.metadata:
                    article.metadata.pop('_author')
                    update_author = True
                
                if not hasattr(article, 'chat_summary'):
                    logger.debug('Skipping article: missing chat_summary')
                    continue
                
                attempted +=1
                if ((attempted+skip)%20) == 0:
                    logger.debug("Index of article in source: %d", attempted+skip)
                # logger.debug(f"Transfering article with url: {article.url}")
                
                response = mapled.article_post(article)
                if isinstance(response, requests.Response):
                    if response.status_code == 400:
                        if update_author:
                            logger.debug(f"Transfering article with url: {json.loads(response.request.body)['url']}")
                            response = mapled.article_put(article)
                            if isinstance(response, Article):
                                logger.debug(f"updated already existing article.")
                            else:
                                logger.warning(f"Failed to update already existing article.")
                    else:
                        logger.warning(f"failed to post the article. response status code {response.status_code}")
                elif isinstance(response, Article):
                    logger.debug(f"Transfering article with url: {article.url}")
                    article_new = response
                    article_new.createDate = article.createDate
                    response = mapled.article_put(article_new)
                    if isinstance(response, Article):
                        transferred +=1
                        logger.debug('article successfully transferred')
                    else:
                        logger.debug(f'failed to update article {response.status_code}')
                
                if n is not None:
                    if transferred >=n and attempted >= n:
                        print_summary(transferred, attempted)
                        return

if __name__ == '__main__':
    args = parser.parse_args() 
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
    )
    
    try:
        maples = MapleAPI(f"http://{args.s}")
        mapled = MapleAPI(f"http://{args.d}")
        transfer(maples=maples, mapled=mapled, n = args.n, skip=args.j)
    except Exception as exc:
        logger.error(exc)

    print (args)
    