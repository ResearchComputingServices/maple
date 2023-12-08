import requests
from requests import exceptions as request_exc

import logging
from maple_structures import Article
from maple_structures import Topic
from maple_structures import Model
from maple_structures import ModelIteration
from maple_structures import Processed

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

    def _delete(self, path: str, uuid: str, timeout=10):
        response = requests.Response()
        try:
            url = f"{self.baseurl}/{path}/{uuid}"
            response = requests.delete(url=url, timeout=timeout)
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
        response = self._post("topic", params=None, body=topic.to_dict(include_model=True))

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

    def model_post(self, model: Model, include_topic: bool = False):
        "Posts a model in the database."

        response = self._post("model", params=None,
                              body=model.to_dict(include_topic=include_topic))

        if response.status_code is not None:
            if response.status_code != 201:
                return response
            try:
                return Model.from_dict(response.json())
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

    def model_get(self):
        response = self._get("model")
        if response.status_code != 200:
            return response
        else:
            try:
                models_json = response.json()
                ret = []
                for model_json in models_json:
                    ret.append(Model.from_dict(model_json))
                return ret
            except Exception as exc:
                logger.error(exc)
                return []

    def model_put(self, model: Model) -> Model:
        response = self._put("model", body=model.to_dict())
        if response.status_code is not None:
            if response.status_code == 200:
                try:
                    return Model.from_dict(response.json())
                except:
                    return response
        return response

    def model_delete(self, uuid: str):
        response = self._delete(path="model", uuid=uuid)
        if response.status_code is not None:
            if response.status_code == 200:
                try:
                    return Model.from_dict(response.json())
                except:
                    return response
        return response

    def model_iteration_post(self, model_iteration: ModelIteration, include_model=True, include_topic=True):
        "Posts a model iteration in the database."
        response = self._post("model-iteration", params=None,
                              body=model_iteration.to_dict(include_model=include_model, include_topic=include_topic))

        if response.status_code is not None:
            if response.status_code != 201:
                return response
            try:
                return ModelIteration.from_dict(response.json())
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

    def model_iteration_get(self):
        response = self._get("model-iteration")
        if response.status_code != 200:
            return response
        else:
            try:
                model_iterations_json = response.json()
                ret = []
                for model_iteration_json in model_iterations_json:
                    ret.append(ModelIteration.from_dict(model_iteration_json))
                return ret
            except Exception as exc:
                logger.error(exc)
                return []

    def model_iteration_put(self, model_iteration: ModelIteration) -> ModelIteration:
        response = self._put("model-iteration", body=model_iteration.to_dict())
        if response.status_code is not None:
            if response.status_code == 200:
                try:
                    return ModelIteration.from_dict(response.json())
                except:
                    return response
        return response

    def model_iteration_delete(self, uuid: str):
        response = self._delete(path="model-iteration", uuid=uuid)
        return response.status_code

    def processed_post_many(self, processed: list[Processed]):
        response = self._post(
            "processed/many", 
            params=None,
            body=[proc.to_dict() for proc in processed])
        
        if response.ok:
            if response.status_code != 201:
                return response
            else:
                return True
        else:
            return response
        
    def processed_post(self, processed: Processed) -> Processed:
        "Posts a processed in the database."
        response = self._post("processed", params=None,
                              body=processed.to_dict())

        if response.status_code is not None:
            if response.status_code != 201:
                return response
            try:
                return Processed.from_dict(response.json())
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

    def processed_get(self, model_iteration_uuid: str, limit: int = None, skip: int= None , as_json: bool = False ):
        params = dict()
        params['modelIteration'] = model_iteration_uuid
        params['limit'] = limit
        params['skip'] = skip
        
        response = self._get("processed", params = params)
        if response.status_code != 200:
            return response
        else:
            try:
                processed_json = response.json()
                if as_json:
                    return processed_json
                ret = []
                for proc_json in processed_json:
                    ret.append(Processed.from_dict(proc_json))
                return ret
            except Exception as exc:
                logger.error(exc)
                return []

    def processed_put(self, processed: Processed) -> Processed:
        response = self._put("processed", body=processed.to_dict())
        if response.status_code is not None:
            if response.status_code == 200:
                try:
                    return Processed.from_dict(response.json())
                except:
                    return response
        return response

    def processed_delete(self, uuid: str):
        response = self._delete(path="processed", uuid=uuid)
        return response.status_code
