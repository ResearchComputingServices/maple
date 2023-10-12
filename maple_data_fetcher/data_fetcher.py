"""fetches data and stores in database"""
import logging
from logging.handlers import RotatingFileHandler
import argparse
import os
import sys
import time
import rcs
from maple_config import config as cfg
sys.path.append(os.path.join(os.path.abspath(""), "newsscrapy"))

print(sys.path)


import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings

scrapy.utils.reactor.install_reactor(
    "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
)
from twisted.internet import defer

defer.setDebugging(True)

from newsscrapy.spiders import scrapyCBC, scrapyCTVNews


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

spiders = [
    scrapyCBC.CBCHeadlinesSpider,
    scrapyCTVNews.CTVNewsSpider,
]


class DataFetcher:
    """class to continuously collect data"""

    def __init__(
        self,
        spiders: list = [scrapyCBC.CBCHeadlinesSpider, scrapyCTVNews.CTVNewsSpider],
        spider_output_file: bool = False,
        spider_log_level: str = "warning",
        spider_interval_sec: int = 120,
        environment= '.env.development'
    ) -> None:
        self.spider_output_file = spider_output_file
        
        self.spider_log_level = spider_log_level
        
        self._environment = environment
        
        self._get_project_settings()
        
        self._spider_interval_sec = spider_interval_sec

        self._spiders = spiders

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

        self._scrapy_settings["ENV"] = "0.0.0.0"

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
    )
    
    logger.debug("args: %s", args)
    logger.debug("config: %s", config)

    data_fetcher = DataFetcher(
        spider_output_file=args.o,
        spider_interval_sec=args.i,
        spider_log_level=args.l,
        environment=env,
    )
    data_fetcher.run()


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
