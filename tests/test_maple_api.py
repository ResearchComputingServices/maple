import unittest
from maple_interface import MapleAPI
from maple_config import config as cfg

class TestMapleAPI(unittest.TestCase):

    def setUp(self):
        config = cfg.load_config(cfg.PRODUCTION)
        self.api = MapleAPI(
            authority=f"http://{config['MAPLE_BACKEND_IP']}:{config['MAPLE_BACKEND_PORT']}")

    def test_get_article_count(self):
        count = self.api.article_count_get()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
    
    def test_article_skip(self):
        articles = self.api.article_get(limit=1)
        article = articles[0]
        articles = self.api.article_get(limit=1, skip=1)
        self.assertNotEqual(article.uuid, articles[0].uuid)
    
    def test_article_iterator(self):
        total_count = self.api.article_count_get()
        skip = total_count  - 2000
        articles = []
        for iterator in self.api.article_iterator(limit=200, page=0, skip=skip):
            articles.extend(iterator)
        self.assertEqual(len(articles), 2000)
            
if __name__ == '__main__':
    unittest.main()
