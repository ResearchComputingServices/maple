'''transfer data from one db to another'''
import logging
import argparse
import requests
from pprint import pprint as p
from maple_structures import Article
from maple_interface import MapleAPI
from maple_config import config as cfg
from maple_processing.process import chat_summary

SUMMARY_KW='chat_summary'

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger("maple_summary")

parser = argparse.ArgumentParser()

parser.add_argument('-b', type= str,required=True, help='the backend ip and port. e.g. 0.0.0.0:3000')
parser.add_argument('-n', type= int, required=False, default=1, help='the number of article to create the summaries')

config = cfg.load_config(cfg.DEVELOPMENT)


def create_summaries(maple: MapleAPI, n: int):
    global config
    if 'MAPLE_CHATGPT35TURBO_APIKEY' in config:
        if config['MAPLE_CHATGPT35TURBO_APIKEY'] is not None:
            converted = 0
            attempted = 0
            while True:
                for articles in maple.article_iterator(limit=1, page=attempted):
                    if len(articles) == 0:
                        return
                    for article in articles:
                        attempted+=1
                        if not hasattr(article, SUMMARY_KW):
                        # if getattr(article, SUMMARY_KW) is not None:
                            
                            try:
                                summary = chat_summary(article.content, config['MAPLE_CHATGPT35TURBO_APIKEY']) 
                                logger.debug("returned a summary with %d words for article %s", len(summary.split(' ')), article.url)
                                setattr(article, SUMMARY_KW, summary)
                                logger.log(9, article.to_dict())
                                ret = maple.article_put(article)
                                if isinstance(ret, Article):
                                    converted +=1
                                else:
                                    logger.warning("Failed to update article. %s", ret)
                            except Exception as exc:
                                logger.error(exc)
                        
                        if (attempted % 20) == 0 or converted >= n:
                            logger.info("Summarized %d/%d attempted articles", converted, attempted)
                        
                        if converted >= n:
                            return
                        
    else: 
        logger.warning('Skipping summary creation because chatgpt key was not properly configured.')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    args = parser.parse_args() 
    logger.debug(args)
    logger.debug("config: %s", config)
    
    try:
        maple = MapleAPI(f"http://{args.b}")
        create_summaries(maple, args.n)
    except Exception as exc:
        logger.error(exc)

    