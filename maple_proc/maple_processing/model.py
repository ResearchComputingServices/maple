import logging
from maple_interface import MapleAPI
from maple_structures import Processed, ModelIteration, Model, Topic

class MapleModel:
    def __init__(self, *args, **kwargs) -> None:
        pass
    
    @classmethod
    def verify_functions(cls):
        required_functions = ['fit', 'transform']
    
    
class MapleProcessing:
    def __init__(
        self, *,
        maple: MapleAPI,
        models = list[MapleModel],
        hours: float = None,
        ):
        self.logger = logging.getLogger('MapleProcessing')
        self.maple_api = maple
        self._models = models
        self._hours = hours
    
    def _create_models(self):
        for modelname, model in zip([f'model_level{i}' for i in range(1,4)], self._models):
            self.logger.debug('Creating model %s of type %s', modelname, type(model))
            setattr(self, modelname, model())
        
    def _classify_all_articles(self):
        for articles in self.maple_api.article_iterator():
            for article in articles:
                processed = Processed()
                for model in [self.model_level1, self.model_level2, self.model_level3]:
                    pass
    
    def _fetch_training_data(self):
        self._training_data = []
        for articles in self.maple_api.article_iterator(hours = self._hours):
            self._training_data.extend(articles)
            
            
    def run(self):
        while True:
            self._model_iteration = ModelIteration()
            self._fetch_training_data()


if __name__ == '__main__':
    TRAINING_HOURS = 24
    maple = MapleAPI(authority='http://localhost:3000')
    maple_proc = MapleProcessing(
        maple=maple, 
        hours=TRAINING_HOURS,
        models=[
            MapleModel(),
            MapleBERT()
        ])
    maple_proc.run()
    pass