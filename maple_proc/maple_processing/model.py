import logging
from maple_structures import Article
from maple_interface import MapleAPI
from maple_structures import Processed, ModelIteration, Model, Topic
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired
from umap import UMAP
import requests
import timeit

logging.getLogger('numba').setLevel(logging.WARNING)

class MapleModel:
    def __init__(self,
                 *args,
                 model_type: str = None,
                 version: str = None,
                 name: str = None,
                 status: str = None,
                 level: int = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        existing_variables = []
        for var in ['type', 'version', 'name', 'status','level']:
            if hasattr(self, var):
                existing_variables.append(var)
        if len(existing_variables) > 0:
            raise ValueError('Variable already exist is supper: %s', existing_variables)
        self.type = model_type or ''
        self.version = version or '1.0'
        self.name = name or ''
        self.status = status or 'created'
        self.level = level or 1
        self.logger = logging.getLogger('maple' if name == '' else f'maple_{name}')
        self._verify_functions()
    
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
    
    def _verify_functions(self):
        required_functions = ['fit', 'transform']
        for fun in required_functions:
            if not hasattr(self, fun):
                raise TypeError('Missing required method %s', fun)
    
    @classmethod
    def create_model(cls, level: int, training_size: int = None):
        raise NotImplementedError('create_model method not implemented.')


class MapleBert(MapleModel, BERTopic):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,
                         model_type = 'bert',
                         version = '1.0',
                         name = 'BERTopic',
                         status = 'created',
                         level = 1,
                         **kwargs)
    
    @classmethod
    def create_model(cls, level: int, training_size: int = None):
        dbscan_kwargs = dict(
            metric = 'euclidean',
            cluster_selection_method = 'eom',
            prediction_data = True,
        )
        
        if level == 1:
            dbscan_kwargs['min_cluster_size'] = 150 if training_size is None else int(training_size/5*0.6)
        elif level == 2:
            dbscan_kwargs['min_cluster_size'] = 50 if training_size is None else int(training_size/25*0.6)
        elif level == 3:
            dbscan_kwargs['min_cluster_size'] = 10 if training_size is None else int(training_size/50*0.6)
        
        MIN_DF = 2
        if dbscan_kwargs['min_cluster_size'] < MIN_DF:
            cls.logger.debug(
                'min_cluster_size (%d) as smaller than MIN_DF (%d). Setting min_cluster_size to MIN_DF',
                dbscan_kwargs['min_cluster_size'],
                MIN_DF)
            dbscan_kwargs['min_cluster_size'] = MIN_DF
            
        hdbscan_model = HDBSCAN(**dbscan_kwargs)
        
        umap_model = UMAP(n_neighbors=15,
                      n_components=5,
                      min_dist=0,
                      metric='cosine',
                      random_state=123)
        
        vectorizer_model = CountVectorizer(
            stop_words='english',
            min_df=2,
            ngram_range=(1,2))
        
        keybert_model = KeyBERTInspired()
        representation_model = {"KeyBERT": keybert_model}
        
        return cls(
            hdbscan_model=hdbscan_model,
            umap_model = umap_model,
            vectorizer_model=vectorizer_model,
            representation_model = representation_model,
            )
        
class MapleProcessing:
    DEBUG_LIMIT_PROCESS_COUNT = 600
    
    def __init__(
        self, *,
        maple: MapleAPI,
        models=list[MapleModel],
        hours: float = None,
        max_hours: float = 30*24,
        article_train_min_size: int = 400,
        debug_limits: bool = False,
        **kwargs,
    ):
        self.logger = logging.getLogger('MapleProcessing')
        self.maple_api = maple
        self._models = models
        self._hours = hours
        self._max_hours = max_hours
        self._article_train_min_size = article_train_min_size
        self._debug_limits = debug_limits
    
    @property
    def models(self):
        return [
            self.model_level1,
            self.model_level2,
            self.model_level3,
        ]
        
    def _create_models(self, model: MapleModel, *args, **kwargs):
        for level in range(1,4):
            modelname = f'model_level{level}'
            self.logger.debug('Creating model %s of type %s',
                              modelname, type(model))
            maple_model = model.create_model(level=level, *args, **kwargs)
            maple_model.level = level
            if level == 1:
                self._model_iteration.type = maple_model.type
                self._model_iteration.name = maple_model.name
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
            time_start = timeit.default_timer()
            
            # remove articles without chat_summaries.
            [articles.remove(article) for article in articles if not hasattr(article, 'chat_summary')]
            
            # extract summaries from articles
            summaries = [article.chat_summary for article in articles]
            
            #create processed objects
            processed_list = []
            for article in articles:
                processed_list.append(
                    Processed(
                        article = article,
                        modelIteration = self._model_iteration,
                        position = [0,0] #TODO compute position using umap
                    )
                )
            
            # classify on all levels, then set the processed filds
            for level in range(1,4):
                self.logger.debug('Classifying %d articles using model %s', len(articles), f'model_level{level}')
                model = getattr(self, f'model_level{level}')
                topic_indexes, probabilities = model.transform(summaries)
                for processed, topic_index, probs in zip(processed_list, topic_indexes, probabilities):
                    topic = [topic for topic in model.model_structure.topic if topic.index == topic_index][0]
                    setattr(processed, f'topic_level{level}', topic)
                    setattr(processed, f'topic_level{level}_prob', probs)
            
            # send all processed objects to backend
            self.logger.debug('Posting %d processed on backend.', len(processed_list))
            for processed in processed_list:
                processed_response = self.maple_api.processed_post(processed)
                if not isinstance(processed_response, Processed):
                    self.logger.warning(f'Failed to post processed for article %s. %s', article.url, processed_response)
                else:
                    self._model_iteration.article_classified += 1
                    if (self._model_iteration.article_classified % 10) == 0:
                        try:
                            self._update_model_iteration()
                        except TypeError as exc:
                            self.logger.error('Failed to update model iteration. %s', exc)
        
            self.logger.info('Classification cycle for %d articles was %f seconds', len(articles), timeit.default_timer()-time_start)
            
            if self._debug_limits:
                if self._model_iteration.article_classified > self.DEBUG_LIMIT_PROCESS_COUNT:
                    break
            
        for level in range(1,4):
            getattr(self._model_iteration, f'model_level{level}').status = 'complete'
        self._update_model_iteration()
        

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

    def _train_models(self, documents: list[str]):
        for level in range(1,4):
            model_name = f'model_level{level}'
            model = getattr(self, model_name, None)
            
            # update status of model on backend
            model_structure = model.model_structure
            model_structure.status = 'training'
            updated_model_structure = self.maple_api.model_put(model_structure)
            if not isinstance(updated_model_structure, Model):
                raise TypeError('Failed to update model_structure')
            else:
                model.model_structure = updated_model_structure
            
            # start training
            start_training_time = timeit.default_timer()
            self.logger.debug('Start training model %s %s', model.name, model_name)
            topics, probs = model.fit_transform(documents)
            training_time = timeit.default_timer() - start_training_time
            self.logger.debug('Training time for model %s %s was %f', model.name, model_name, training_time)

            # for topic_index, topic_label in enumerate(model.topic_labels_):
            model_uuid_mapping = {}
            for topic_key in model.topic_representations_.keys():
                topic_structure = Topic(
                    name = model.topic_labels_[topic_key],
                    keyword =  [k[0] for k in model.topic_representations_[topic_key]],
                    label = model.topic_representations_[topic_key][0][0], #TODO use chat_gpt to grab best describing word
                    index = topic_key,
                    # dot_summary = [],
                    prevalence = model.topic_sizes_[topic_key]/len(documents),
                    model=model_structure
                )
                #TODO calculate center for topic
                
                topic_structure_created=self.maple_api.topic_post(topic_structure)
                if not isinstance(topic_structure, Topic):
                    raise TypeError('Could not create a topic')
                else:
                    model_structure.add_topic(topic_structure_created)
                
            
            #TODO save model
            #TODO send model to backend
            
        # update model iteration on backend
        self._model_iteration.article_trained = len(documents)
        
        ## TODO try catch
        self._update_model_iteration()
        
    def _update_model_iteration(self):
        if not hasattr(self, '_model_iteration'):
            raise AttributeError("Missing _model_iteration attribute.")
        updated_model_structure = self.maple_api.model_iteration_put(self._model_iteration)    
        if not isinstance(updated_model_structure, ModelIteration):
            raise TypeError('Failed to update model structure')
        else:
            self._model_iteration = updated_model_structure
            self.model_level1.model_structure = self._model_iteration.model_level1
            self.model_level2.model_structure = self._model_iteration.model_level2
            self.model_level3.model_structure = self._model_iteration.model_level3
            
            
    def run(self, *, run_once: bool = False):
        run_count = 0
        while True:
            run_count += 1
            if run_once and run_count > 1:
                break
            
            # Fetch training data.
            try:
                self._fetch_training_data()
                summaries = self._extract_chat_summaries(self._training_data)
            except ValueError as exc:
                self.logger.info('Could not retrieve enough data. %s', exc)
                continue
            
            # create a model iteration and models
            for model in self._models:
                # Model iteration that will be used to keep track of models and status
                self._model_iteration = ModelIteration()
                              
                # Create models for all levels
                self._create_models(model, training_size=len(self._training_data))
                
                self._train_models(documents=summaries)
                
                self._classify_all_articles()
                
                
                

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.INFO)

    TRAINING_HOURS = 24
    maple = MapleAPI(authority='http://localhost:3000')
    maple_proc = MapleProcessing(
        maple=maple,
        hours=TRAINING_HOURS,
        models=[
            # MapleModel,
            MapleBert,
            # MapleLDA,
        ],
        debug_limits=True)
    maple_proc.run(run_once=True)
    pass
