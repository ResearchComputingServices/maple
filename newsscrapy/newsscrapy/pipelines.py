# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from maple_interface import MapleAPI
from maple_structures import Article


class NewsscrapyPipeline:

    maple = MapleAPI("http://0.0.0.0:3000", apiversion="api/v1")

    def process_item(self, item, spider):
        try:
            self.maple.article_post(Article.from_json(item))
        except Exception as exc:
            self.logger.error(exc)
        return item
