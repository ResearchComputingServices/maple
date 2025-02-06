import asyncio
from json import load
import unittest
from requests import Response
from maple_config.config import load_config
from maple_interface import MapleAPI
from maple_processing.process import personalized_summary, personalized_topic_name


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

class TestPersonalizedRequests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(None)
        self.config = load_config(environment="development")
        
        self.maple = MapleAPI(
            authority="http://localhost:3000")
        self.backend_config = self.maple.config_get()
        
    
    async def test_personalized_summary(self):
        config = self.backend_config
        article = self.maple.article_get(limit=1)
        article = article[0]
        # TODO remove comment and implement in backend.
        # prompt = config['prompts']['default']
        
        prompt = None
        if config['model']['selectedModel'] in config['prompts']:
            prompt = config['prompts'][config['model']['selectedModel']]['summary']
        elif config['model']['default'] in config['prompts']:
            prompt = config['prompts'][config['model']['default']]['summary']    
        
        response = await personalized_summary(
            host = config['model']['host'],
            port= config['model']['port'],
            api_key=config['model']['api_key'],
            model_type=config['model']['selectedModel'],
            prompt=prompt,
            content=article.content,
            )
        
        print(response)
        
    async def test_personalized_topic_name(self):  
        config = self.backend_config
        keywords = "politics, canada, immigration, refugees, economy"
        
        response = await personalized_topic_name(
            host = config['model']['host'],
            port= config['model']['port'],
            api_key=config['model']['api_key'],
            model_type=config['model']['selectedModel'],
            keywords=[k.strip() for k in keywords.split(',')],
            )
        
        print(response)
