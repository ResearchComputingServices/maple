import logging
import os
import shutil
from umap import UMAP
import timeit
import time
import random
import json
from sentence_transformers import SentenceTransformer
from requests import Response
from maple_chatgpt.chatgpt_client import ChatgptClient
from maple_processing.process import chatgpt_bullet_summary
from maple_structures import Article
from maple_interface import MapleAPI
from maple_structures import Processed, ModelIteration, Model, Topic
from .model import MapleBert, MapleModel


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
        chatgpt_client: ChatgptClient = None,
        model_iteration_datapath: str = 'data',
        # **kwargs,
    ):
        self.logger = logging.getLogger('MapleProcessing')
        self.maple_api = maple
        self._models = models
        self._hours = hours
        self._max_hours = max_hours
        self._article_train_min_size = article_train_min_size
        self._debug_limits = debug_limits
        self._chatgpt_client = chatgpt_client
        self._model_iteration_datapath = model_iteration_datapath
        self._init_vars()

    def _init_vars(self):
        self.model_level1 = None
        self.model_level2 = None
        self.model_level3 = None
        self._model_iteration = ModelIteration()
        self._training_data = []
        self._article_classified = []
        self._processed = []
        
        
    @property
    def models(self):
        return [
            self.model_level1,
            self.model_level2,
            self.model_level3,
        ]

    def _maple_embed_documents(self, documents: list[str]):
        if not hasattr(self, '_sentence_transformer'):
            self._sentence_transformer = SentenceTransformer(
                'all-MiniLM-L6-v2')
        return self._sentence_transformer.encode(documents)

    def _detect_positions(self, documents: list[str], fit: bool = False):
        embeddings = self._maple_embed_documents(documents)
        if not hasattr(self, '_umap_model'):
            self._umap_model = UMAP(n_neighbors=10, n_components=2, min_dist=0.0,
                                    metric='cosine')
        if fit:
            self._umap_model.fit(embeddings)
        positions = self._umap_model.transform(embeddings)
        return positions

    def _create_models(self, model: MapleModel, *args, **kwargs):
        for level in range(1, 4):
            modelname = f'model_level{level}'
            self.logger.debug('Creating model %s of type %s',
                              modelname, type(model))
            maple_model = model.create_model(level=level, *args, **kwargs)
            maple_model.level = level
            if level == 1:
                self._model_iteration.type = maple_model.type
                self._model_iteration.name = maple_model.name
            setattr(self, modelname, maple_model)
            self._model_iteration.add_model_level(
                modelname, maple_model.model_structure)

        # Update database: create model_iteration and models.
        model_iteration = self.maple_api.model_iteration_post(
            self._model_iteration)
        if isinstance(model_iteration, Response):
            raise TypeError('Failed to post model_iteration')
        elif isinstance(model_iteration, ModelIteration):
            self._model_iteration = model_iteration
            self.model_level1.model_structure = model_iteration.model_level1
            self.model_level2.model_structure = model_iteration.model_level2
            self.model_level3.model_structure = model_iteration.model_level3

    def _classify_all_articles(self):
        self._model_iteration.article_classified = 0
        # update status to classifying
        for level in range(1, 4):
            getattr(self._model_iteration,
                    f'model_level{level}').status = 'classifying'
        self._update_model_iteration()

        for articles_it in self.maple_api.article_iterator(limit=100, page=0):
            time_start = timeit.default_timer()

            # remove articles without chat_summaries.
            articles = []
            for article in articles_it:
                if hasattr(article, 'chat_summary'):
                    articles.append(article)

            if len(articles) == 0:
                continue

            # extract summaries from articles
            summaries = []
            for article in articles:
                summary = getattr(article, 'chat_summary', None)
                if not summary:
                    self.logger.error(
                        'Missing chat_summary for article %s %s', article.uuid, article.url)
                    raise ValueError(
                        f'Missing chat_summary for article {article.uuid} {article.url}')
                summaries.append(summary)

            positions = self._detect_positions(summaries)

            # create processed objects
            processed_list = []
            for article, position in zip(articles, positions.tolist()):
                processed_list.append(
                    Processed(
                        article=article,
                        modelIteration=self._model_iteration,
                        position=position,
                    )
                )

            # classify on all levels, then set the processed fields
            for level in range(1, 4):
                self.logger.debug('Classifying %d articles using model %s', len(
                    articles), f'model_level{level}')
                model = getattr(self, f'model_level{level}')
                topic_indexes, probabilities = model.transform(summaries)
                for processed, topic_index, probs in zip(processed_list, topic_indexes, probabilities):
                    topic = [
                        topic for topic in model.model_structure.topic if topic.index == topic_index][0]
                    setattr(processed, f'topic_level{level}', topic)
                    setattr(processed, f'topic_level{level}_prob', probs)

            # send all processed objects to backend
            self.logger.debug(
                'Posting %d processed on backend.', len(processed_list))
            try:
                response = self.maple_api.processed_post_many(processed_list)
                if isinstance(response, Response):
                    self.logger.warning(
                        'Failed to post batch of Processed. Trying one at a time.')
                    for processed in processed_list:
                        processed_response = self.maple_api.processed_post(
                            processed)
                        if not isinstance(processed_response, Processed):
                            self.logger.warning(
                                'Failed to post processed for article %s. %s',
                                article.url,
                                processed_response)
                        else:
                            self._model_iteration.article_classified += 1
                            if (self._model_iteration.article_classified % 10) == 0:
                                try:
                                    self._update_model_iteration()
                                except TypeError as exc:
                                    self.logger.error(
                                        'Failed to update model iteration. %s', exc)
                else:
                    self._model_iteration.article_classified += len(
                        processed_list)
                    self._update_model_iteration()
                
                # store articles and processed
                for var in ['_article_classified', '_processed']:
                    if not hasattr(self, var):
                        setattr(self, var, [])

                getattr(
                    self,
                    '_article_classified'
                ).extend(articles)
                
                getattr(
                    self,
                    '_processed',
                ).extend(processed_list)
                
            except Exception as exc:
                self.logger.error('Failed to post processed. %s', exc)

            self.logger.info('Classification cycle for %d articles was %f seconds. %d articles classified.', len(
                articles), timeit.default_timer()-time_start, self._model_iteration.article_classified)

            if self._debug_limits:
                if self._model_iteration.article_classified >= self.DEBUG_LIMIT_PROCESS_COUNT:
                    break

        for level in range(1, 4):
            getattr(self._model_iteration,
                    f'model_level{level}').status = 'complete'
        self._update_model_iteration()

    # def _classify_articles(self, articles: list[Article], create_processed: bool = True):
    #     pass

    def _fetch_training_data(self):
        # Fetch data until minimum number of articles are reached.
        article_hours = self._hours
        self._training_data = []

        flag_message = False
        while len(self._training_data) < self._article_train_min_size:
            self._training_data = []
            for articles in self.maple_api.article_iterator(hours=article_hours):
                for article in articles:
                    if hasattr(article, 'chat_summary'):
                        self._training_data.append(article)
            article_hours += 12
            if flag_message:
                self.logger.debug(
                    "Increasing number of hours to achieve article_train_min_size: %d", article_hours)
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
        for level in range(1, 4):
            model_name = f'model_level{level}'
            model = getattr(self, model_name, None)

            # update status of model on backend
            model_structure = model.model_structure
            model_structure.status = 'training'

            model_structure = self._update_model_structure(level, model_structure=model_structure)

            # start training
            start_training_time = timeit.default_timer()
            self.logger.debug('Start training model %s %s',
                              model.name, model_name)
            _, _ = model.fit_transform(documents)
            training_time = timeit.default_timer() - start_training_time
            
            self.logger.debug('Training time for model %s %s was %f',
                              model.name, model_name, training_time)

            # Create topics on dababase
            topic_info = model.maple_get_topic_info()
            for topic in topic_info:
                if topic.prevalence < 0:
                    topic.prevalence = 0
                if topic.prevalence > 1:
                    topic.prevalence = 1
                    
                topic_structure = Topic(
                    name = topic.name,
                    keyword = topic.keyword,
                    label = topic.label,
                    index= topic.index,
                    prevalence = topic.prevalence,
                    model = model_structure
                )
                topic_structure = self._update_topic_structure(
                    level=level,
                    topic=topic_structure)
                
                self._chatgpt_topic_name(topic=topic_structure)
                self._chatgpt_topic_bullet_summary(
                    topic=topic_structure, 
                    representative_docs=topic.representative_docs)

            # update model_structure with topics
            model_structure = self._update_model_structure(level=level, model_structure=model_structure)

            model_path = os.path.join(
                self._model_iteration_datapath,
                self._model_iteration.uuid,
                f'model_level{level}')
            os.makedirs(model_path, exist_ok=True)
            model.maple_save(model_path=model_path)
            
            # update model iteration on backend
            self._model_iteration.article_trained = len(documents)

            # TODO try catch
            self._update_model_iteration()

    def _chatgpt_topic_bullet_summary(self, topic: Topic, representative_docs: list[str] ):
        data=dict(
            uuid = topic.uuid,
            content = representative_docs,
        )
        self._chatgpt_client.request_bullet_summary(
            topic=data
        )
    
    def _chatgpt_topic_name(self, topic: Topic):
        data = dict(
            uuid = topic.uuid,
            keyword = topic.keyword,
        )
        self._chatgpt_client.request_topic_name(
            topic=data,
            until_success=True,
        )
        
    def _chatgpt_tasks(self):
        resent_time = time.time()
        resent_count = 0
        wait_time = len(self._chatgpt_client.sent_jobs) * 10
        while(len(self._chatgpt_client.sent_jobs) != 0):
            if resent_count == 0 or (time.time()-resent_time >= wait_time):
                resent_time = time.time()
                resent_count+=1
                self.logger.debug('Resubmitting chatgpt jobs.')
                self._chatgpt_client.resubmit_jobs()
                wait_time = len(self._chatgpt_client.sent_jobs) * 20
                self.logger.debug('wait for %.2f seconds', wait_time)
        
        
        topic_mapping=dict()
        
        for level in range(1,4):
            model_name = f"model_level{level}"
            model = getattr(self, model_name)
            for topic in model.model_structure.topic:
                if topic.uuid:
                    topic_mapping[topic.uuid] = topic

        def get_topic_name_mapping():
            topic_name_mapping = dict()
            for t in self._chatgpt_client.topic_name_results:
                topic_name_mapping[t['job_details']['uuid']]=t
            return topic_name_mapping
        
        def get_topic_bullet_mapping():
            topic_bullet_mapping = dict()
            for t in self._chatgpt_client.topic_bullet_summary_results:
                topic_bullet_mapping[t['job_details']['uuid']] = t
            return topic_bullet_mapping

        def check_missing_keys(pkey, skey):
            return [key for key in pkey if key not in skey]
        
        while True:
            missing_keys = check_missing_keys(topic_mapping.keys(), get_topic_name_mapping().keys())
            if  len(missing_keys) != 0:
                self.logger.warning('Still missing requests for topic name from chatgpt for topic uuids: %s', missing_keys)
                #TODO resubmit jobs.
                time.sleep(random.random()*2)
            else:
                break
        
        while True:
            missing_keys = check_missing_keys(topic_mapping.keys(), get_topic_bullet_mapping().keys())
            if  len(missing_keys) != 0:
                self.logger.warning('Still missing requests for topic name from chatgpt for topic uuids: %s', missing_keys)
                #TODO resubmit jobs.
                time.sleep(random.random()*2)
            else:
                break
        
        #TODO update topics
        topic_bullet_mapping = get_topic_bullet_mapping()
        topic_name_mapping = get_topic_name_mapping()
        
        topic_levels = dict()
        for level in range(1,4):
            model = getattr(self, f"model_level{level}")
            for topic in model.model_structure.topic:
                topic_levels[topic.uuid] = level
        
        for topic_uuid, topic in topic_mapping.items():
            topic.label = topic_name_mapping[topic.uuid]['results']
            topic.dot_summary = topic_bullet_mapping[topic.uuid]['results']
            self._update_topic_structure(
                level=topic_levels[topic_uuid],
                topic=topic
            )
        
    
    def _update_topic_structure(self, level: int, topic: Topic):
        model_name = f"model_level{level}"
        
        model = getattr(self, model_name)
        topic_in_model_structure = None
        for i, t in enumerate(model.model_structure.topic):
            if t.index==topic.index:
                topic_in_model_structure = i
                break
        
        if topic_in_model_structure is None:
            while True:
                updated_topic = self.maple_api.topic_post(topic)
                if isinstance(updated_topic, Topic):
                    topic = updated_topic
                    model.model_structure.add_topic(topic)
                    break
                else:
                    self.logger.warning('Failed to post topic. Reattempting... %s', updated_topic)
                    time.sleep(random.random()*2)
        else:
            while True:
                updated_topic = self.maple_api.topic_put(topic)
                if isinstance(updated_topic, Topic):
                    topic=updated_topic
                    model.model_structure.topic[topic_in_model_structure] = topic
                    break
                else:
                    self.logger.warning("Failed updating topic. Reattempting... %s", updated_topic)
        return topic
                
    def _update_model_structure(self, level: int, model_structure: Model):
        while True:
            updated_model_structure = self.maple_api.model_put(model_structure)
            if isinstance(updated_model_structure, Model):
                model_structure = updated_model_structure
                break
            else:
                self.logger.warning(
                    'Failed to update model structure. %s', 
                    updated_model_structure)
                wait_time = random.random()*2
                self.logger.debug("reattempt in %.2f seconds", wait_time)
                time.sleep(wait_time)
                continue
            
        setattr(self._model_iteration, f"model_level{level}", model_structure)
        setattr(
            getattr(self, f"model_level{level}"),
            'model_structure',
            model_structure
        )
        return getattr(self._model_iteration, f"model_level{level}")
        
    def _update_model_iteration(self):
        """Updates the model iteration in the backend.

        Raises:
            AttributeError: _description_
            TypeError: _description_
        """        
        if not hasattr(self, '_model_iteration'):
            raise AttributeError("Missing _model_iteration attribute.")
        #TODO retrieve chatgpt updates.
        
        updated_model_structure = self.maple_api.model_iteration_put(
            self._model_iteration)
        if not isinstance(updated_model_structure, ModelIteration):
            raise TypeError('Failed to update model structure')
        else:
            self._model_iteration = updated_model_structure
            self.model_level1.model_structure = self._model_iteration.model_level1
            self.model_level2.model_structure = self._model_iteration.model_level2
            self.model_level3.model_structure = self._model_iteration.model_level3
    
    def _store_data(self):
        """Stores the data associated to a model iteration in zip format.
        Values were created across different functions.
        """
        article_out = []
        for article in self._article_classified:
            article_out.append(
                dict(
                    uuid=article.uuid,
                    url = article.url,
                    content = article.chat_summary
                )
            )
        
        processed_out = []
        for processed in self._processed:
            processed_out.append(
                processed.to_dict()
            )
        
        path = os.path.join(
            self._model_iteration_datapath,
            self._model_iteration.uuid)
        os.makedirs(path, exist_ok=True)
        
        to_store = [
            dict(value=article_out, name='article.json'),
            dict(value=processed_out, name='processed.json'),
            dict(value=self._model_iteration.to_dict(), name='model_iteration.json'),
        ]
        for var_to_store in to_store:
            try:
                with open(os.path.join(path, var_to_store['name']), 'w', encoding='utf-8') as file:
                    json.dump(var_to_store['value'], file, indent=2)
            except Exception as exc:
                self.logger.error('Failed to store file %s. %s', var_to_store['name'], exc)
        
        # zip directory now.
        shutil.make_archive(path, 'zip', path)
        # remove original directory
        shutil.rmtree(path)

    def _cleanup(self):
        self._chatgpt_client.sent_jobs = dict()
        self._chatgpt_client.topic_bullet_summary_results = []
        self._chatgpt_client.topic_name_results = []
        
    def run(self, *, run_once: bool = False):
        run_count = 0
        while True:
            self._init_vars()
            iteration_time_start = timeit.default_timer()
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

            # self._create_sentence_transformer()
            # embeddings = self._maple_embed_documents(summaries)
            self._detect_positions(summaries, fit=True)

            # create a model iteration and models
            for model in self._models:
                # Model iteration that will be used to keep track of models and status
                self._model_iteration = ModelIteration()

                # Create models for all levels
                self._create_models(
                    model, training_size=len(self._training_data))

                self._train_models(documents=summaries)

                self._classify_all_articles()
                
                self._chatgpt_tasks()
                
                self._store_data()
                
                self._cleanup()
                
            iteration_time = timeit.default_timer()-iteration_time_start
            self.logger.info('Iteration for %s ended in %.2f seconds',
                             self._model_iteration.name, iteration_time)
