import scrapy
import json
import re
from urllib.parse import urlparse, urljoin, urlsplit, urlunparse
import validators
from datetime import datetime
from maple import Article, Comments, Author
import logging
from _news.utils import get_date_str

logging.basicConfig()
logger = logging.getLogger("scapyCBC")
logging.getLogger('scrapy').propagate = False

class CBCArticleExtractor:
    
    @staticmethod
    def extract_author(response, data: dict = None):
        out = []
        try:
            selector = response.xpath('//div[@class="authorprofile"]')
            if len(selector) == 0:
                return out
        except Exception as e:
            logger.debug(f"extract_author: failed to retrieve author profiles. {e}")
            return out
        author = None
        if data is not None:
            if any (key in Author._default_keys for key in data.keys()):
                author = Author.from_json(data)
        if author is None:
            author = Author()
        
        for i, authorselector in enumerate(selector.xpath('//div[@class="authorprofile-container"]')):
            if i > 0:
                author = Author()
            # set name
            if getattr(author, 'name', '')  == '':
                author.name = authorselector.xpath('//div[@class="authorprofile-name-container"]//a//text()').get()
            # set url
            if getattr(author, 'url', '') == '':
                try:
                    url = authorselector.xpath('//div[@class="authorprofile-name-container"]/a/@href').get()
                    if url:
                        if not validators.url(url):
                            parsed = urlparse(response.url)
                            url = f"{parsed.scheme}://{parsed.netloc}{url}"
                    author.url = url
                except:
                    logger.debug(f"extract_author:Could not retrieve url for author. {e}")
            
            if getattr(author, 'title', '') == '':
                title = authorselector.xpath('//p[@class="authorprofile-title"]//text()').get()
                if title is not None:
                    try:
                        author.title = title
                    except Exception as e:
                        logger.debug(f"extract_author:Could not set author title. {e}")
            
            #about
            if getattr(author, 'about', '') == '':
                try:
                    about = authorselector.xpath('//p[@class="authorprofile-biography"]//text()').get()
                    author.about = about
                    email = None
                    try:
                        email_search = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', about)
                        if email_search is not None:
                            email = email_search.group(0).strip().rstrip('.')
                        if email is not None:
                            author.email=email
                    except Exception as e:
                        logging.debug(f"extract_author:Could not set email {email}. {e}")
                except Exception as e:
                    logger.debug(f"extract_author:Could not retrieve author biography. {e}")
                    
            out.append(author)                                           
            
        return out
        
        
    @staticmethod
    def from_response(response, extra: dict = {}):
        article = Article()
        
        if 'title' in extra.keys():
            article.title = extra.pop('title')
        else:
            article.title = response.xpath('//h1[@class="detailHeadline"]//text()').get()
        
        article.url = response.url
        
        article.content = '\n'.join(response.xpath('//div[@class="story"]//text()').getall())
        
        if 'author' in extra.keys():
            authors = CBCArticleExtractor.extract_author(response)
            try:
                article.author = authors
            except Exception as e:
                logger.debug(f"from_response:Could not set authors. {e}")
        
        try:
            article.content = '\n'.join(response.xpath('//div[@class="story"]//text()').getall())
        except Exception as e:
            logger.debug(f"from_response:Could not fetch content. {e}")
        
        summary=None
        if 'description' in extra.keys():
            if extra['description'] != '':
                summary = [extra['description']]
        if summary is None:
            summary = response.xpath('//div[@class="detailSummary"]//text()').getall()
        if summary:
            try:
                article.summary='\n'.join(summary)
            except Exception as e:
                logger.debug(f"from_response:Could not set summary. {e}")
        
        date_published = None
        if 'publishTime' in extra.keys():
            try:
                if isinstance(extra['publishTime'], int):
                    date_published = get_date_str(extra['publishTime']/1000)
            except Exception as e:
                logger.debug(f"from_response:Could not convert datetime from {extra['publishTime']}. {e}")
        if date_published is None:
            #TODO fetch from body
            pass
        if date_published is not None:
            try:
                article.date_published = date_published
            except Exception as e:
                logger.debug(f"from_response:Could not set date_published from {date_published}. {e}")
        
        date_modified = None
        if 'updateTime' in extra.keys():
            try:
                if isinstance(extra['updateTime'], int):
                    date_modified = get_date_str(extra['updateTime']/1000)
            except Exception as e:
                logger.debug(f"from_response: could not fetch modified date from {extra['updateTime']}. {e}")
        if date_modified is not None:
            try:
                article.date_modified = date_modified
            except Exception as e:
                logger.debug(f"from_response:Could not set article field date_modified from: {date_modified}. {e}")
        
        return article
    
    
class CBCHeadlinesSpider(scrapy.Spider):
    url_mapping = dict()
    name = "CBC News"
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        
        base_url = "https://cbc.ca/news/canada"
        
        locations = [
            "British Columbia",
            "Calgary",
            "Edmonton",
            "Saskatchewan",
            "Saskatoon",
            "Manitoba",
            "Thunder Bay",
            "Sudbury",
            "Windsor",
            "London",
            "Kitchener-Waterloo",
            "Hamilton",
            "Toronto",
            "Ottawa",
            "Montreal",
            "New Brunswick",
            "Prince Edward Island",
            "Nova Scotia",
            "Newfoundland & Labrador",
            "North",
            ]
        
        location_links = [str.replace(re.sub('[ˆ\W]\s', '', location), " ", "-").lower() for location in locations]
        
        for location_link in location_links:
            self.start_urls.append(f"{base_url}/{location_link}")
        
        
    def start_requests(self):
        yield scrapy.Request(url='https://www.cbc.ca/rss', callback=self.get_rss_sources)
        for link in self.start_urls:
            yield scrapy.Request(url=link, callback=self.parse)
            
    def get_rss_sources(self, response):
        for rssfeedlink in response.xpath('//td[@class="rssfeed"]//text()').getall():
            yield scrapy.Request(url=rssfeedlink, callback=self.get_rss_news)
        
    def get_rss_news(self, response):
        for link in response.xpath('//item//link//text()').getall():
            url = link.split('?')[0]
            if url not in self.url_mapping.keys():
                self.url_mapping[url] = {}
                yield scrapy.Request(url=url, callback=self.parse_news_content)
        
    def parse(self, response):
        pattern = r'\bwindow.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;'
        json_data = response.xpath('//script[@id="initialStateDom"]').re_first(pattern)
        data = json.loads(json_data)
        try:
            for news_content in data['content']['list']:
                try:
                    url = news_content['itemURL']
                    if url not in self.url_mapping.keys():
                        self.url_mapping[url] = news_content
                        yield scrapy.Request(url=url, callback=self.parse_news_content)
                except:
                    pass
        except:
            pass
        
        
    def parse_news_content(self, response):
        if response.url not in self.url_mapping.keys():
            return None
        article = CBCArticleExtractor.from_response(response=response, extra=self.url_mapping[response.url])
        return article.to_dict()

def save_response_body(response):
    try:
        with open('out.html', 'w') as f:
            f.write(str(response.body))
    except:
        print('Could not store output.')