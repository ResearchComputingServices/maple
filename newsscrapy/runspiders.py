"""Continuously run spiders"""
import logging
import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from newsscrapy.spiders.scrapyCBC import CBCHeadlinesSpider
from newsscrapy.spiders.scrapyCTVNews import CTVNewsSpider
from twisted.internet import reactor
import glob
import os
import shutil
import json
import requests
import time
from maple_structures import Article
from maple_interface import MapleAPI

# scrapy.utils.log.configure_logging(install_root_handler=False)
# logging.basicConfig(level=logging.ERROR)

maple = MapleAPI("http://0.0.0.0:3000", apiversion="api/v1")


def crawl_jobs():
    """Job to start spiders."""
    settings = get_project_settings()

    # FEEDS = {'results.json' : {'format':'json'}}
    settings["FEED_FORMAT"] = "json"
    settings["FEED_URI"] = "data/%(time)s_%(name)s_results_Roger.json"
    settings["LOG_LEVEL"] = "ERROR"

    runner = CrawlerRunner(settings)
    return [
        runner.crawl(CBCHeadlinesSpider),
        runner.crawl(CTVNewsSpider),
    ]


def schedule_next_crawl(null, sleep_time):
    reactor.callLater(sleep_time, crawl)


def crawl():
    jobs = crawl_jobs()
    for job in jobs:
        job.addCallback(schedule_next_crawl, 60)
        job.addErrback(catch_error)


def catch_error(failure):
    print(failure.value)


if __name__ == "__main__":
    crawl()
    reactor.run()

# process = CrawlerProcess(settings=settings)
# while True:
#     process.crawl(CBCHeadlinesSpider)
#     process.crawl(CTVNewsSpider)
#     process.start()

#     files = glob.glob("data/*.json")
#     count = 0
#     for file in files:
#         articles = json.load(open(file, "r", encoding="utf-8"))
#         for article in articles:
#             response = maple.article_post(Article.from_json(article))
#             if isinstance(response, Article):
#                 print(f"article stored from {response.url}")
#             elif isinstance(response, requests.Response):
#                 print(response.json())

#         # print(articles[0])

#         if not os.path.exists("data/to_process"):
#             os.makedirs("data/to_process")

#         shutil.move(file, "data/to_process/" + os.path.split(file)[-1])

#     SLEEP_TIME = 10
#     print(f"Sleep for {SLEEP_TIME} seconds")
#     time.sleep(SLEEP_TIME)
#     # break
