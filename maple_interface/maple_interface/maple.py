import requests
from requests import exceptions as request_exc

import logging
from maple_structures import Article

logger = logging.getLogger("MapleAPI")


class Articles:
    def __init__(self, authority, *, apiversion="api/v1", hours: int = None, samples: int = 10) -> None:
        self._authority = authority
        self._apiversion = apiversion
        self._hours = hours
        self._samples = samples
    
    # def __iter__(self)

class MapleAPI:
    def __init__(self, authority, *, apiversion="api/v1", suppress_errors=True) -> None:
        self._authority = authority
        self._apiversion = apiversion
        self._suppress_errors = suppress_errors

    @property
    def baseurl(self):
        '''baseurl is the encoded url'''
        return f"{self._authority}/{self._apiversion}"
    
    def _post(self, path: str, headers=None, params=None, body=None):
        response = requests.Response()
        try:
            url = f"{self.baseurl}/{path}"
            response = requests.post(url, headers=headers, params=params, json=body)
        except Exception as exc:
            logger.error(f"post: {url}. {exc}")
        return response

    def _put(self, path: str, headers=None, params=None, body=None):
        try:
            url = f"{self.baseurl}/{path}"
            requests.put()
            response = requests.get(url=url, headers=headers,params=params, json=body)
        except Exception as exc:
            logger.error(exc)
        return response

    def _get(self, url, headers=None, params=None):
        try:
            url = f"{self._authority}/{path}"
            response = requests.get(url=url, headers=headers, params=params)
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
        response = self._put('article', body=article.to_dict())
        if response.status_code is not None:
            if response.status_code == 200:
                return Article.from_json(response.json())
        return response

    def article_get(self):
        pass
