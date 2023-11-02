import requests
from requests import exceptions as request_exc

import logging
from maple_structures import Article
from maple_structures import Topic

logger = logging.getLogger("MapleAPI")


class Articles:
    def __init__(
        self,
        mapleapi,
        limit: int = 100,
        page: int = 0,
        hours: int = None
    ) -> None:
        self._mapleapi = mapleapi
        self._limit = limit
        self._page_start = page
        self._hours = hours

    def __iter__(self):
        self._page = self._page_start
        # if self._page is not None:
        #     self._page +=1
        return self

    def __next__(self):
        articles = self._mapleapi.article_get(
            limit=self._limit, page=self._page, hours=self._hours)

        if isinstance(articles, requests.Response):
            raise StopIteration
        if len(articles) == 0:
            raise StopIteration
        self._page += 1
        return articles


class MapleAPI:
    def __init__(self, authority, *, apiversion="api/v1", suppress_errors=True) -> None:
        self._authority = authority
        self._apiversion = apiversion
        self._suppress_errors = suppress_errors

    @property
    def baseurl(self):
        """baseurl is the encoded url"""
        return f"{self._authority}/{self._apiversion}"

    def _post(self, path: str, headers=None, params=None, body=None, timeout=10):
        response = requests.Response()
        try:
            url = f"{self.baseurl}/{path}"
            response = requests.post(
                url, headers=headers, params=params, json=body, timeout=timeout)
        except Exception as exc:
            logger.error(f"post: {url}. {exc}")
        return response

    def _put(self, path: str, headers=None, params=None, body=None, timeout=10):
        response = requests.Response()
        try:
            url = f"{self.baseurl}/{path}"
            response = requests.put(
                url=url, headers=headers, params=params, json=body, timeout=timeout)
        except Exception as exc:
            logger.error(exc)
        return response

    def _get(self, path: str, headers=None, params=None, timeout=10):
        response = requests.Response()
        try:
            url = f"{self.baseurl}/{path}"
            response = requests.get(
                url=url, headers=headers, params=params, timeout=timeout)
        except Exception as exc:
            logger.error(exc)
        return response

    def article_post(self, article: Article, update: bool = False):
        "Posts an article in the database."
        response = self._post("article", params=None, body=article.to_dict())

        if response.status_code is not None:
            if response.status_code != 201:
                return response
            try:
                return Article.from_json(response.json())
            except request_exc.ConnectionError as exc:
                logger.error("No connection to backend server. %s", exc)
            except Exception as exc:
                if self._suppress_errors:
                    return None
                else:
                    raise exc
        else:
            if not self._suppress_errors:
                raise ConnectionError()
            return {}

    def article_put(self, article: Article) -> Article:
        response = self._put("article", body=article.to_dict())
        if response.status_code is not None:
            if response.status_code == 200:
                try:
                    return Article.from_json(response.json())
                except:
                    return response
        return response

    def article_get(
            self,
            limit: int = None,
            page: int = None,
            hours: int = None,
            url: str = None,
            uuid: str = None):
        params = dict()
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page
        if hours is not None:
            params["hours"] = hours
        if url is not None:
            params["url"] = url
        if uuid is not None:
            params['uuid'] = uuid
        response = self._get("article", params=params)
        if response.status_code != 200:
            return response
        else:
            try:
                articles_json = response.json()
                ret = []
                for article_json in articles_json:
                    ret.append(Article.from_json(article_json))
                return ret
            except Exception as exc:
                logger.error(exc)
                return []

    def article_iterator(self, limit: int = 100, page: int = None, hours: int = None):
        '''function to iterate through articles.'''
        return iter(Articles(
            self,
            limit=limit if limit is not None else 100,
            page=page if page is not None else 0,
            hours=hours))
        # while True:
        #     articles = self.article_get(limit, page, hours)
        #     if isinstance(articles, requests.Response):
        #         yield []
        #     # if len(articles) == 0:
        #     #     return articles
        #     page += 1
        #     yield articles

    def topic_post(self, topic: Topic):
        "Posts a topic in the database."
        response = self._post("topic", params=None, body=topic.to_dict())

        if response.status_code is not None:
            if response.status_code != 201:
                return response
            try:
                return Topic.from_dict(response.json())
            except request_exc.ConnectionError as exc:
                logger.error("No connection to backend server. %s", exc)
            except Exception as exc:
                if self._suppress_errors:
                    return None
                else:
                    raise exc
        else:
            if not self._suppress_errors:
                raise ConnectionError()
            return {}

    def topic_get(self):
        response = self._get("topic")
        if response.status_code != 200:
            return response
        else:
            try:
                topics_json = response.json()
                ret = []
                for topic_json in topics_json:
                    ret.append(Topic.from_dict(topic_json))
                return ret
            except Exception as exc:
                logger.error(exc)
                return []

    def topic_put(self, topic: Topic) -> Topic:
        response = self._put("topic", body=topic.to_dict())
        if response.status_code is not None:
            if response.status_code == 200:
                try:
                    return Topic.from_dict(response.json())
                except:
                    return response
        return response
