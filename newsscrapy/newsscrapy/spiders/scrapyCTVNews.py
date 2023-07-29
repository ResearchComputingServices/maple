import scrapy
import json
import logging
from maple import Article, Author
import validators

# logging.getLogger('scrapy').propagate = False

class CTVNewsSpider(scrapy.Spider):
    name="ctvnews"
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.base_url = 'https://www.ctvnews.ca'
        self.start_urls = [
            f'https://www.ctvnews.ca/more/rss-feeds-for-ctv-news',
        ]
        self.url_mapping = {}
        
    def parse(self, response):
        if response:
            for url in response.xpath('//div[@class="content-primary"]//a//@href').getall():
                yield scrapy.Request(url, self.parse_rss_link)

    def parse_rss_link(self, response):
        if response:
            for url in response.xpath('//item//link//text()').getall():
                yield scrapy.Request(url=url, callback=self.parse_news_content)

    
    def parse_news_content(self, response):
        if not response:
            return
        if response.url in self.url_mapping.keys():
            return

        article = Article()
        
        article.url = response.url
        
        try:
            data = json.loads(response.xpath('//script[@type="application/ld+json"]//text()').get(), strict=False)
        except:
            data = {}
        
        if 'headline' in data.keys():
            try:
                article.title = data['headline']
            except:
                article.title = self._extract_title(response)
        
        if 'author' in data.keys():
            for dataauthor in data['author']:
                if '@type'in dataauthor.keys():
                    if dataauthor['@type'] == 'Person':
                        author = Author()
                        if 'name' in dataauthor.keys():
                            author.name = dataauthor['name']
                        if 'sameAs' in dataauthor.keys():
                            try:
                                if not isinstance(dataauthor['sameAs'], list):
                                    dataauthorlist = [dataauthor['sameAs']]
                                for dataauthorcontact in dataauthor['sameAs']:
                                    if validators.url(dataauthorcontact):
                                        author.url = dataauthorcontact
                                    if validators.email(dataauthorcontact):
                                        author.email = dataauthorcontact
                            except:
                                self.logger.debug(f"Could not set url for author {author.name}: {dataauthor['sameAs']}")
                        article.add_author(author)
        
        content = response.xpath('//div[@class="c-text"]//text()').getall()
        if content:
            article.content = '\n'.join(content)
        
        possible_urls = response.xpath('//div[@class="c-text"]//a//@href').getall()
        if possible_urls:
            for url in possible_urls:
                if self.base_url in url:
                    self.logger.debug(f"Found related news url {url}")
                    yield scrapy.Request(url=url, callback=self.parse_news_content)
        
        # Not a valid article
        if (article.title == '' and article.content == ''):
            return
        self.url_mapping[response.url] = article.to_dict()
        yield article.to_dict()
    
    def _extract_title(self, response):
        title = response.xpath('//div//h1[@class="c-title__text"]//text()').get()
        if title:
            return title
        else:
            return ''