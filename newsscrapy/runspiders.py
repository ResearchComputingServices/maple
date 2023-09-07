import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from newsscrapy.spiders.scrapyCBC import CBCHeadlinesSpider
from newsscrapy.spiders.scrapyCTVNews import CTVNewsSpider
import glob
import os
import shutil
import json
import requests
from maple_structures import Article
from maple_interface import MapleAPI

maple = MapleAPI('http://0.0.0.0:3000',apiversion='api/v1')

settings = get_project_settings()

# FEEDS = {'results.json' : {'format':'json'}}
settings["FEED_FORMAT"] = "json"
settings["FEED_URI"] = "data/%(time)s_%(name)s_results_Roger.json"

process = CrawlerProcess(settings=settings)
while True:
    process.crawl(CBCHeadlinesSpider)
    process.crawl(CTVNewsSpider)
    process.start()

    files = glob.glob("data/*.json")
    for file in files:
        articles = json.load(open(file, 'r', encoding='utf-8'))
        for article in articles:
            response = maple.article_post(Article.from_json(article))
            if isinstance(response, Article):
                print(f"article stored from {response.url}")
            elif isinstance(response, requests.Response):
                print(response.json())
        
        # print(articles[0])
        
        if not os.path.exists("data/to_process"):
            os.makedirs("data/to_process")
                          
        shutil.move(file, "data/to_process/" + os.path.split(file)[-1])

    break
    