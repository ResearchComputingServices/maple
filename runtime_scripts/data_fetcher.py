"""fetches data and stores in database"""
import logging
import argparse
import os
import sys
import scrapy
import numpy as np
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import defer

import rcs
from maple_interface.maple import MapleAPI

from maple_config import config as cfg
 
sys.path.append(os.path.join(os.path.abspath(""), "newsscrapy"))
sys.path.append(os.path.join(os.path.abspath(""), "../newsscrapy"))
from newsscrapy.spiders import scrapyCBC, scrapyCTVNews, CTVNewsV2

print(sys.path)




scrapy.utils.reactor.install_reactor(
    "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
)


defer.setDebugging(True)




parser = argparse.ArgumentParser(
    prog="Maple data fetcher",
    description="Fetches data and stores in the database.",
    epilog="Maple data fetcher",
)

parser.add_argument(
    "-o",
    action="store_true",
    help="stores the output of each spider each time the spider is executed",
)

parser.add_argument(
    "-e", choices=["dev", "prod"], default="dev", help="the environment to use"
)

parser.add_argument("-i", type=int, help="the interval in which each spider should run")

parser.add_argument(
    "-l",
    choices=["debug", "info", "warn", "error", "critical"],
    default="info",
    help="log level",
)


logger = logging.getLogger("data_fetcher")

spiders_ = [
    scrapyCBC.CBCHeadlinesSpider,
    # scrapyCTVNews.CTVNewsSpider,
    CTVNewsV2.CTVNewsSpider,
]


class DataFetcher:
    """class to continuously collect data"""

    def __init__(
        self,
        backend_ip: str,
        backend_port: str,
        spiders: list = [scrapyCBC.CBCHeadlinesSpider, scrapyCTVNews.CTVNewsSpider],
        spider_output_file: bool = False,
        spider_log_level: str = "warning",
        spider_interval_sec: int = 120,
        environment= '.env.development',
        
    ) -> None:
        self.spider_output_file = spider_output_file
        
        self.spider_log_level = spider_log_level
        
        self._environment = environment
        
        self._get_project_settings()
        
        self._spider_interval_sec = spider_interval_sec

        self._spiders = spiders
        
        self._maple_api = MapleAPI(
            f"http://{backend_ip}:{backend_port}"
        )

    def _update_spider_interval_sec_from_config(self):
        if self._environment == '.env.development':
            logger.info("Development environment. Not updating spider interval from config.")
            return
        config = self._maple_api.config_get()
        if isinstance(config, dict):
            if 'spider_interval_seconds' in config:
                if self._spider_interval_sec != config['spider_interval_seconds']:
                    logger.info("Updating spider interval from %s to %s", self._spider_interval_sec, config['spider_interval_seconds'])
                    self._spider_interval_sec = config['spider_interval_seconds']
            elif config == {}:
                logger.warning("Failed to retrieve config from backend. Using last updated spider interval.")    
            else:
                logger.error("spider_interval_seconds not found in config.")
        else:
            logger.warning("Failed to get config from backend. Using last updated spider interval.")
        
    def _get_project_settings(self):
        self._scrapy_settings = get_project_settings()

        if self.spider_output_file:
            self._scrapy_settings["FEEDS"] = {
                "data/%(time)s_results_spider_%(name)s.json": {"format": "json"}
            }

        self._scrapy_settings["LOG_LEVEL"] = self.spider_log_level.upper()
        self._scrapy_settings["REQUEST_FINGERPRINTER_IMPLEMENTATION"] = "2.7"

        self._scrapy_settings[
            "TWISTED_REACTOR"
        ] = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

        self._scrapy_settings["ITEM_PIPELINES"] = {
            "newsscrapy.pipelines.NewsscrapyPipeline": 300
        }
        
        self._scrapy_settings["MAPLE_ENVIRONMENT"] = self._environment
        
        self._scrapy_settings["COOKIES_ENABLED"] = False
        self._scrapy_settings["DOWNLOAD_DELAY"] = np.random.uniform(1.1, 3.5)
        self._scrapy_settings["RANDOMIZE_DOWNLOAD_DELAY"] = True
        
        # self._scrapy_settings["USER_AGENT"]= "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; http://www.google.com/bot.html) Chrome/W.X.Y.Z‡ Safari/537.36"
        # user_agent_keywords = [
        #     "Ambitious",
        #     "Helpful",
        #     "Adventurous",
        #     "Bright",
        #     "Cheerful",
        #     "Considerate",
        #     "Courageous",
        #     "Adaptable",
        #     "Affable",
        #     "Affectionate",
        #     "Agreeable",
        #     "Attentive",
        #     "Authentic",
        #     "Brave",
        #     "Calm",
        #     "Creative",
        #     "Diligent",
        #     "Empathetic",
        #     "Witty",
        #     "Amazing",
        #     "Amiable",
        #     "Amicable",
        #     "Compassionate",
        #     "Curious"
        # ]
        # user_agent_adjectives = [f"{np.random.choice(user_agent_keywords)}" for _ in range(np.random.randint(2, 5))]
        # user_agent_name = 'And'.join(user_agent_adjectives)
        # self._scrapy_settings["USER_AGENT"]= f"my-{user_agent_name}-project (http://{'example'}.com)"
        
        self._scrapy_settings["DOWNLOADER_MIDDLEWARES"] = {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
            'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        }
        
        self._scrapy_settings["FAKEUSERAGENT_PROVIDERS"] = [
            'scrapy_fake_useragent.providers.FakerProvider',
            'scrapy_fake_useragent.providers.FakeUserAgentProvider',     
            'scrapy_fake_useragent.providers.FixedUserAgentProvider',
        ]
        
        # If using proxies, should include them here.
        # self._scrapy_settings["ROTATING_PROXY_LIST"] = [
        #     'http://proxy1.com:8000',
        #     'http://proxy2.com:8031',
        #     # Add more proxies here
        # ]
        
        self._scrapy_settings["AUTOTHROTTLE_ENABLED"] = True
        self._scrapy_settings["AUTOTHROTTLE_START_DELAY"] = 1
        self._scrapy_settings["AUTOTHROTTLE_MAX_DELAY"] = 10
        self._scrapy_settings["AUTOTHROTTLE_TARGET_CONCURRENCY"] = 1.0
        self._scrapy_settings["AUTOTHROTTLE_DEBUG"] = False
        
        self._scrapy_settings["ENV"] = "0.0.0.0"
        logging.debug(self._scrapy_settings)

    def _crawl_job(self, spider):
        """create the crawl job"""
        logger.info("_crawl_job: %s", spider)
        self._get_project_settings()
        runner = CrawlerRunner(self._scrapy_settings)
        return runner.crawl(spider)

    def _schedule_next_crawl(self, _, sleep_time, spider):
        """schedule next crawl"""
        logger.info("_schedule_next_crawl: %s, %s", sleep_time, spider)
        logger.info("Scheduling call for spider %s", spider)
        from twisted.internet import reactor

        reactor.callLater(sleep_time, self._crawl, spider)

    def _catch_error(self, failure):
        """catch error needed for scrapy"""
        logger.info("_catch_error %s", failure)
        logger.error(failure.value)

    def _crawl(self, spider):
        """crawl a spider and set callback to schedule next crawl"""
        logger.info("Crawling spider: %s", spider)
        # Fetch config from backend to update interval in case it changed.
        self._update_spider_interval_sec_from_config()
        job = self._crawl_job(spider)
        job.addCallback(self._schedule_next_crawl, self._spider_interval_sec, spider)
        # job.errback(self._catch_error)

    def _crawl_initial(self):
        """initialize the crawling"""
        logger.info("_crawl_initial")
        for spider in self._spiders:
            self._crawl(spider)

    def run(self):
        from twisted.internet import reactor

        self._crawl_initial()
        reactor.run()


def main(args):
    env = None
    if args.e == "dev":
        env = cfg.DEVELOPMENT
    elif args.e == "prod":
        env = cfg.PRODUCTION
    else:
        env = args.e

    config = cfg.load_config(env)

    if args.i is None:
        args.i = int(config['MAPLE_DATA_FETCHER_SPIDERS_INTERVAL_SECONDS'])

    rcs.utils.configure_logging(
        level = args.l,
        output_directory='logs',
        output_filename_prefix='data_fetcher',
        output_file_max_size_bytes=5e6,
        n_log_files = 4,
        use_postfix_hour = False
    )
    
    logger.debug("args: %s", args)
    logger.debug("config: %s", config)

    data_fetcher = DataFetcher(
        backend_ip=config['MAPLE_BACKEND_IP'],
        backend_port=config['MAPLE_BACKEND_PORT'],
        spiders=spiders_,
        spider_output_file=args.o,
        spider_interval_sec=args.i,
        spider_log_level=args.l,
        environment=env,
    )
    data_fetcher.run()


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)