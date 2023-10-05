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
parser.add_argument('--only_chat', action="store_true", help="Transfer only articles with chatGPT summaries.")

def print_summary(transferred, attempted, updated):
    logger.info(f"Summary:\ntransferred {transferred}/{attempted} articles.\nIt also updated {updated} articles")

def article_cleanup(maple: MapleAPI):
    updated = 0
    total_articles = 0
    for articles in maple.article_iterator(limit=100):
        total_articles +=1
        for article in articles:
            update=False
            if '_author' in article.metadata:
                update=True
                article['metadata'].pop('_author')
            
            if update:
                maple.article_put(article)
                updated +=1
        if (total_articles % 10) == 0:
            logger.debug("article cleanup updated  %d/%d articles", updated, total_articles)
    logger.info("article clenup updated  %d/%d articles", updated, total_articles)
    
                

def transfer(maples: MapleAPI, 
             mapled: MapleAPI, 
             n: int, 
             skip: int, 
             only_chat = True):
    '''transfer articles from one backend to another'''
    transferred = 0
    attempted = 0
    updated_count =0
    n_articles_per_page = 100
    for articles in maples.article_iterator(limit=n_articles_per_page, page=int(skip/n_articles_per_page)):
        # if len(articles) == 0:
        #     print_summary(transferred, attempted)
        #     return
        for article in articles:
            
            update_author = False
            if '_author' in article.metadata:
                article.metadata.pop('_author')
                update_author = True
            
            if only_chat:
                if not hasattr(article, 'chat_summary'):
                    logger.debug('Skipping article: missing chat_summary (%s)', article.url)
                    continue
            
            attempted +=1
            if ((attempted+skip)%20) == 0:
                logger.debug("Index of article in source: %d", attempted+skip)
            # logger.debug(f"Transfering article with url: {article.url}")
            
            # check if article already exists in db
            articled = mapled.article_get(url=article.url)
            if len(articled) > 0:
                if isinstance(articled[0], Article):
                    # article exists in destination
                    if not hasattr(articled[0],"chat_summary"):
                        # should update article
                        article.uuid = articled[0].uuid
                        article_updated = mapled.article_put(article)
                        if isinstance(article_updated, Article):
                            logger.debug("updated article %s to %s (%s)", article.uuid, article_updated.uuid, article.url)
                            article=article_updated
                            updated_count +=1
                            continue
                        else:
                            logger.error("Failed udpating article %s", article_updated)
                    else:
                        continue
            
            response = mapled.article_post(article)
            if isinstance(response, requests.Response):
                logger.error("failed to post article %s", response)
                # if response.status_code == 400:
                #     if update_author:
                #         logger.debug(f"Transfering article with url: {json.loads(response.request.body)['url']}")
                #         response = mapled.article_put(article)
                #         if isinstance(response, Article):
                #             logger.debug(f"updated already existing article.")
                #         else:
                #             logger.warning(f"Failed to update already existing article.")
                # else:
                #     logger.warning(f"failed to post the article. response status code {response.status_code}")
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
                    print_summary(transferred, attempted, updated_count)
                    return
    print_summary(transferred, attempted, updated_count)

if __name__ == '__main__':
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
    )
    logging.debug("Provided arguments %s", args)
    
    try:
        maples = MapleAPI(f"http://{args.s}")
        mapled = MapleAPI(f"http://{args.d}")
        # article_cleanup(maples)
        transfer(maples=maples, mapled=mapled, n = args.n, skip=args.j)
    except Exception as exc:
        logger.error(exc)

    print (args)
    