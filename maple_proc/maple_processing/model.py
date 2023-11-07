import logging
from maple_structures import Article
from maple_interface import MapleAPI
from maple_structures import Processed, ModelIteration, Model, Topic
from bertopic import BERTopic
import requests

class MapleModel:
    def __init__(self, *args, **kwargs) -> None:
        self.type = ''
        self.version = ''
        self.name = ''
        self.status = 'created'
        self.level = 1
    
    @property
    def model_structure(self):
        if hasattr(self, '_model_structure'):
            return getattr(self, '_model_structure')
        model = Model()
        model.type = self.type
        model.version = self.version
        model.name = self.name
        model.status = self.status
        model.level = self.level
        setattr(self, '_model_structure', model)
        return model
    
    @model_structure.setter
    def model_structure(self, model: Model):
        setattr(self, '_model_structure', model)
    
    @classmethod
    def verify_functions(cls):
        required_functions = ['fit', 'transform']
        for fun in required_functions:
            if not hasattr(cls, fun):
                raise TypeError('Missing required method %s', fun)


class MapleBert(MapleModel, BERTopic):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.type = 'bert'
        self.version = '1.0'
        self.name = 'BERTopic'
        self.status = 'created'
        self.level = 1
        


class MapleProcessing:
    def __init__(
        self, *,
        maple: MapleAPI,
        models=list[MapleModel],
        hours: float = None,
        max_hours: float = 30*24,
        article_train_min_size: int = 400,
        **kwargs,
    ):
        self.logger = logging.getLogger('MapleProcessing')
        self.maple_api = maple
        self._models = models
        self._hours = hours
        self._max_hours = max_hours
        self._article_train_min_size = article_train_min_size
    
    @property
    def models(self):
        return [
            self.model_level1,
            self.model_level2,
            self.model_level3
        ]
        
    def _create_models(self, model: MapleModel):
        for level in range(1,4):
            modelname = f'model_level{level}'
            self.logger.debug('Creating model %s of type %s',
                              modelname, type(model))
            maple_model = model()
            maple_model.level = level
            setattr(self, modelname, maple_model)
            self._model_iteration.add_model_level(modelname, maple_model.model_structure)
        
        # Update database: create model_iteration and models.
        model_iteration = self.maple_api.model_iteration_post(self._model_iteration)
        if isinstance(model_iteration, requests.Response):
            raise TypeError('Failed to post model_iteration')
        elif isinstance(model_iteration, ModelIteration):
            self._model_iteration = model_iteration
            self.model_level1.model_structure = model_iteration.model_level1
            self.model_level2.model_structure = model_iteration.model_level2
            self.model_level3.model_structure = model_iteration.model_level3
                        

    def _classify_all_articles(self):
        
        self._model_iteration.article_classified = 0 
        for articles in self.maple_api.article_iterator():
            for article in articles:
                if hasattr(article, 'chat_summary'):
                    self._model_iteration.article_classified += 1
                    processed = Processed()
                    for model in [self.model_level1, self.model_level2, self.model_level3]:
                        pass

    def _fetch_training_data(self):
        # Fetch data until minimum number of articles are reached.
        article_hours = self._hours
        self._training_data = []

        flag_message=False
        while len(self._training_data) < self._article_train_min_size:
            self._training_data = []
            for articles in self.maple_api.article_iterator(hours=article_hours):
                for article in articles:
                    if hasattr(article, 'chat_summary'):
                        self._training_data.append(article)
            article_hours += 12
            if flag_message:
                self.logger.debug("Increasing number of hours to achieve article_train_min_size: %d", article_hours)
            flag_message = True
            if article_hours > self._max_hours:
                raise ValueError(
                    "Number of hours used for trained reached max_hours without having enough articles for training")
        self.logger.info('Retrieved %d articles', len(self._training_data))
    
    def _extract_chat_summaries(self, data: list[Article]):
        summaries = []
        for article in data:
            if hasattr(article, 'chat_summary'):
                summaries.append(article.chat_summary)
        return summaries

    def run(self, *, run_once: bool = False):
        run_count = 0
        while True:
            run_count += 1
            if run_once and run_count > 1:
                break
            
            # Fetch training data.
            try:
                self._fetch_training_data()
            except ValueError as exc:
                self.logger.info('Could not retrieve enough data. %s', exc)
                continue
            
            # create a model iteration and models
            for model in self._models:
                # Model iteration that will be used to keep track of models and status
                self._model_iteration = ModelIteration()
                
                # Create models for all levels
                self._create_models(model)
                
                self._model_iteration.article_trained = len(self._training_data)
                self._model_iteration.type = model_level1.type
                
                
                



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.INFO)

    model1 = MapleBert()
    print(isinstance(model1, MapleModel))
    TRAINING_HOURS = 24
    maple = MapleAPI(authority='http://localhost:3000')
    maple_proc = MapleProcessing(
        maple=maple,
        hours=TRAINING_HOURS,
        models=[
            # MapleModel,
            MapleBert
        ])
    maple_proc.run(run_once=True)
    pass
