import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from newsscrapy.spiders.scrapyCBC import CBCHeadlinesSpider
from newsscrapy.spiders.scrapyCTVNews import CTVNewsSpider
import glob
import os
import shutil

settings = get_project_settings()

# FEEDS = {'results.json' : {'format':'json'}}
settings["FEED_FORMAT"] = "json"
settings["FEED_URI"] = "data/%(time)s_%(name)s_results_Roger.json"

process = CrawlerProcess(settings=settings)
process.crawl(CBCHeadlinesSpider)
process.crawl(CTVNewsSpider)
process.start()

files = glob.glob("data/*.json")
for file in files:
    shutil.move(file, "data/to_process/" + os.path.split(file)[-1])
