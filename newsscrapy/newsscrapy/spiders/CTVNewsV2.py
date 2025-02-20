

import os
import glob
from typing import Union
import re
import json
import logging

from scrapy.spiders import Spider
from scrapy.http import HtmlResponse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from playwright.async_api import async_playwright

from maple_structures import Article, Author

logger = logging.getLogger("CTVNewsSpider")

class CTVNewsParser:
    @staticmethod
    def parse_article(response: HtmlResponse) -> Union[Article, None]:
        article = None
        try:
            article = CTVNewsParser.parse_from_json(response)
        except json.JSONDecodeError as e:
            logger.warning('Error parsing article from JSON: %s', e)
            
        if article is None:
            try:
                article = CTVNewsParser.parse_from_html(response)
            except NotImplementedError as e:
                logger.warning('HTML parsing not implemented: %s', e)
            except Exception as e:
                logger.warning('Error parsing article from HTML: %s', e)
                
        return article
        
    
    @staticmethod
    def parse_from_json(response: HtmlResponse) -> Union[Article, None]:
        js = response.xpath('//script[@id="fusion-metadata"]//text()').extract_first()
        
        if js:
            match = re.search(r'Fusion\.globalContent\s*=\s*({.*?});', js, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                article = Article()
                article.url = response.url
                
                # Title
                if 'headlines' in data:
                    if 'basic' in data['headlines']:
                        article.title = data['headlines']['basic']
                # Content
                if 'content_elements' in data:
                    if isinstance(data['content_elements'], list):
                        content = article.title
                        for element in data['content_elements']:
                            if 'type' in element and element['type'] == 'text':
                                if 'content' in element:
                                    content += '\n' + element['content']
                            elif 'type' in element and element['type'] == 'header':
                                if 'content' in element:
                                    content += '\n' + element['content'] + '\n'
                            else: 
                                if 'content' in element:
                                    content += ' ' + element['content']
                        article.content = content
                # Date Published
                if 'first_publish_date' in data:
                    article.date_published = data['first_publish_date']
                elif 'publish_date' in data:
                    article.date_published = data['publish_date']
                if 'last_updated_date' in data:
                    article.date_modified = data['last_updated_date']
                
                if 'language' in data:
                    article.language = data['language']
                
                # Authors
                if 'credits' in data:
                    if 'by' in data['credits']:
                        for author in data['credits']['by']:
                            new_author = Author()
                            if 'additional_properties' in author:
                                if 'original' in author['additional_properties']:
                                    original = author['additional_properties']['original']
                                    name = ''
                                    if 'firstName' in  original:
                                        name += original['firstName']
                                    if 'lastName' in original:
                                        name += ' ' + original['lastName']
                                    new_author.name = name
                                    
                                    if 'email' in original:
                                        new_author.email = original['email']
                                    else:
                                        new_author.email = None
                                    if 'bio_page' in original:
                                        new_author.url = response.urljoin(original['bio_page'])
                            
                            # if best format is not found, try to parse from other fields
                            elif 'type' in author and author['type'] == 'author':
                                if 'name' in author:
                                    new_author.name = author['name']
                                if 'url' in author:
                                    new_author.url = response.urljoin(author['url'])
                                if 'social_links' in author:
                                    if 'url' in author['social_links']:
                                        if 'site' in author['social_links'] and author['social_links']['site'] == 'email':
                                            new_author.email = author['social_links']['url']
                            if new_author.name != '':
                                article.add_author(new_author)
                return article
        raise ValueError('Article not found in JSON')
    
    @staticmethod
    def parse_from_html(response: HtmlResponse) -> Union[Article, None]:
        raise NotImplementedError()


class CTVNewsSpider(Spider):
    name = 'CTVNewsSpider'
    sample_file_location = None
    
    def __init__(self, on_article_content: callable = None, **kwargs):
        super().__init__(self.name, **kwargs)
        self.start_urls = ['https://www.ctvnews.ca']
        self.on_article_content = on_article_content   
        self.visited = []
        self.count=0
        if self.sample_file_location is not None:
            os.makedirs(self.sample_file_location, exist_ok=True)
        
    async def parse(self, response):
        if response.url in self.visited:
            yield None
        self.visited.append(response.url)
        for href in response.css('a::attr(href)').getall():
            if self.start_urls[0] in href or href.startswith('/'):
                if '/article/' in href:
                    yield await self.parse_article(response.urljoin(href))
                else:
                    yield response.follow(href, self.parse)
            else:
                print(f'Invalid external link: {href}')
                
    async def parse_article(self, url):
        article = None
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url) # , wait_until='networkidle'
            
            content = await page.content()
            htmlresponse = HtmlResponse(url=page.url, body=content, encoding='utf-8')
            
            article = CTVNewsParser.parse_article(htmlresponse)
            
            if self.sample_file_location is not None:
                # Store screenshot
                await page.screenshot(
                    path=os.path.join(self.sample_file_location, f'{self.count}-screen.png'),
                    full_page=True)
                
                # Store article JSON
                json.dump(article.to_dict(), open(os.path.join(self.sample_file_location, f'{self.count}-article.json'), 'w', encoding='utf-8'), indent=4)
                
                # Store HTML content
                html = htmlresponse.body.decode('utf-8')
                with open(
                    os.path.join(self.sample_file_location,f'{self.count}-contenthtml.html'),
                    'w',
                    encoding='utf-8') as file:
                    file.write(html)
                
            browser.close()
            self.count += 1
            
        return article.to_dict()
    

if __name__ == "__main__":

    SAMPLE_FOLDER = 'sample3'
    
    # cleanup sample folder.
    files = glob.glob(os.path.join(SAMPLE_FOLDER, '*'))
    for f in files:
        os.remove(f)
        
    settings = get_project_settings()
    settings['PLAYWRIGHT_BROWSER_TYPE'] = 'chromium'
    settings['PLAYWRIGHT_LAUNCH_OPTIONS'] = {'headless': True}
    settings['ROBOTSTXT_OBEY'] = True
    
    process = CrawlerProcess(settings=settings)
    CTVNewsSpider.sample_file_location = SAMPLE_FOLDER
    process.crawl(CTVNewsSpider)
    process.start()