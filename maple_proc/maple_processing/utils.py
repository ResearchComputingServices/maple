"""utils have helper functions"""
import glob
import os
import json
from json.decoder import JSONDecodeError
import logging
from maple_structures import Article

logger = logging.getLogger("atlin_proc:utils")


def load_articles(path: str) -> list:
    """load articles exported from the spiders."""
    out = []
    existing_urls = []
    data = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except JSONDecodeError as exc:
                logger.error("Could not load data from file %s. %s", path, exc)
    elif os.path.isdir(path):
        files = glob.glob(os.path.join(path, "*.json"))
        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data += json.load(file)
            except JSONDecodeError as exc:
                logger.error("Could not load data from file %s. %s", path, exc)
                raise exc
    else:
        raise ValueError(f"Invalid path: {path}")
    for article_json in data:
        if article_json["url"] not in existing_urls:
            existing_urls.append(article_json["url"])
            out.append(Article.from_json(article_json))

    return out
