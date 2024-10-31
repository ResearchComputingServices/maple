import unittest
from requests import Response
from maple_interface import MapleAPI


class TestConfigGet(unittest.TestCase):
    def setUp(self) -> None:
        self.maple = MapleAPI(
            authority="http://localhost:3000")
        
    def test_config_get(self):
        config = self.maple.config_get()
        if isinstance(config, Response):
            print("Could not reach the server")
        else:
            self.assertTrue(isinstance(config, dict))
            keys = [
                "article_summary_length",
                "max_bullet_points",
                "model_iteration_persistence_days",
                "spider_interval_seconds",
                ]
            for key in keys:
                self.assertTrue(key in config, f"Key {key} not found in config")
        
        print(config)
        