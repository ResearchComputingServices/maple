"""Continuously run spiders"""
import logging

import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
scrapy.utils.reactor.install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

from newsscrapy.spiders.scrapyCBC import CBCHeadlinesSpider
from newsscrapy.spiders.scrapyCTVNews import CTVNewsSpider

import glob
import os
import shutil
import json
import requests
import time
from maple_structures import Article
from maple_interface import MapleAPI

print(f"Is asyncio reactor installed: {scrapy.utils.reactor.is_asyncio_reactor_installed()}")

maple = MapleAPI("http://0.0.0.0:3000", apiversion="api/v1")

def crawl_jobs():
    """Job to start spiders."""
    settings = get_project_settings()
    settings['FEEDS'] = {'data/%(time)s_results_spider_%(name)s.json' : {'format':'json'}}
    settings["LOG_LEVEL"] = "DEBUG"
    settings['TWISTED_REACTOR']= "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
    settings['ITEM_PIPELINES'] = {"newsscrapy.pipelines.NewsscrapyPipeline": 300}
    print(settings.__dict__['attributes']['ITEM_PIPELINES'])
    runner = CrawlerRunner(settings)
    
    
    return [
        runner.crawl(CBCHeadlinesSpider),
        # runner.crawl(CTVNewsSpider),
    ]


def schedule_next_crawl(null, sleep_time):
    from twisted.internet import reactor
    print(f'Scheduling next call {time.strftime("%H:%M:%S", time.localtime())}')
    reactor.callLater(sleep_time, crawl)
    files = glob.glob('data/*.json')
    print (files)


def crawl():
    jobs = crawl_jobs()
    for i, job in enumerate(jobs):
        if i == 0:
            job.addCallback(schedule_next_crawl, 10)
        job.addErrback(catch_error)


def catch_error(failure):
    print(failure.value)


if __name__ == "__main__":
    from twisted.internet import reactor
    logging.basicConfig(level=logging.INFO, filename=None)
    crawl()
    reactor.run()
