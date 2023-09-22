'''Test api calls. Backend should be running.'''
from uuid import uuid4
import requests
from maple_structures import Article
from maple_interface import MapleAPI



maple = MapleAPI("http://127.0.0.1:3000")
FAKE_ARTICLE = False

if FAKE_ARTICLE:
    article = Article()
    article.url = f'http://www.google.com/news2s{uuid4()}'
    # article.url = "http://www.google.com/news2s"
    article.content = "Some random content"
    article.title = "Title of the article."

    print(article.to_dict())

    article_result = maple.article_post(article)
    if isinstance(article_result, requests.Response):
        print(
            f"Failed to post article. Response {article_result.status_code}.\n{article_result.json()}"
        )
    elif article_result is None:
        pass
    else:
        print(article_result.to_dict())



