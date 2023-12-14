import logging
import os
import shutil
from attr import has
from httpx import get
from torch import Value
from umap import UMAP
import timeit
import time
import random
import json
import requests
from sentence_transformers import SentenceTransformer
from requests import Response
from copy import deepcopy
from rtpt_research import RTPTResearch
from maple_chatgpt.chatgpt_client import ChatgptClient
# from maple_processing.process import chatgpt_bullet_summary
from maple_structures import Article
from maple_interface import MapleAPI
from maple_structures import Processed, ModelIteration, Model, Topic
from .model import MapleBert, MapleModel


class MapleProcessing:
    DEBUG_LIMIT_PROCESS_COUNT = 2000
    ARTICLE_PAGE_SIZE=1000

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

    @property
    def model_iteration_path(self):
        if not hasattr(self, '_model_iteration_datapath'):
            raise AttributeError('Missing model iteration datapath')
        if not hasattr(self, '_model_iteration'):
            raise AttributeError('Missing _model_iteration')
        if self._model_iteration.uuid is None:
            raise ValueError("Model iteration should have a uuid")
        return os.path.join(
            self._model_iteration_datapath,
            self._model_iteration.uuid)
        
    def _maple_embed_documents(self, documents: list[str]):
        if not hasattr(self, '_sentence_transformer'):
            self._sentence_transformer = SentenceTransformer(
                'all-MiniLM-L6-v2')
        return self._sentence_transformer.encode(documents)

    def _detect_positions(self, documents: list[str], fit: bool = False):
        tstart = timeit.default_timer()
        embeddings = self._maple_embed_documents(documents)
        if not hasattr(self, '_umap_model'):
            self._umap_model = UMAP(n_neighbors=10, n_components=2, min_dist=0.0,
                                    metric='cosine')
        if fit:
            self._umap_model.fit(embeddings)
        positions = self._umap_model.transform(embeddings)
        self.logger.debug("Time for _detect_positions: %.2fs", timeit.default_timer()-tstart)
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
        self._update_model_iteration(keep_fields=['article_classified'])
        # update status to classifying
        for level in range(1, 4):
            model_structure = getattr(self._model_iteration, f'model_level{level}')
            model_structure.status = 'classifying'
            self._update_model_structure(
                level=level,
                model_structure=model_structure,
                keep_fields=['status'])
        

        for articles_it in self.maple_api.article_iterator(limit=self.ARTICLE_PAGE_SIZE, page=0):
            time_start = timeit.default_timer()

            # remove articles without chat_summaries.
            articles = []
            for article in articles_it:
                if hasattr(article, 'chat_summary'):
                    articles.append(article)

            if len(articles) == 0:
                continue

            # extract summaries from articles
            tstart_summaries = timeit.default_timer()
            summaries = self._extract_chat_summaries(articles)
            self.logger.debug("Extract summaries: %.2fs", timeit.default_timer()-tstart_summaries)
            
            tstart_positions = timeit.default_timer()
            positions = self._detect_positions(summaries)
            self.logger.debug("Detect positions: %.2fs",timeit.default_timer()-tstart_positions)
            
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
                tstart = timeit.default_timer()
                self.logger.debug('Classifying %d articles using model %s', len(
                    articles), f'model_level{level}')
                model = getattr(self, f'model_level{level}')
                topic_indexes, probabilities = model.transform(summaries)
                for processed, topic_index, probs in zip(processed_list, topic_indexes, probabilities):
                    topic = [
                        topic for topic in model.model_structure.topic if topic.index == topic_index][0]
                    setattr(processed, f'topic_level{level}', topic)
                    setattr(processed, f'topic_level{level}_prob', probs)
                elapsed=timeit.default_timer()-tstart
                self.logger.debug("Classification time: %.2fs", elapsed)
            # send all processed objects to backend
            self.logger.debug(
                'Posting %d processed on backend.', len(processed_list))
            try:
                tstart_post = timeit.default_timer()
                response = self.maple_api.processed_post_many(processed_list)
                
                if isinstance(response, Response):
                    self.logger.warning("Failed to post processed. %s, %d", response, response.status_code)
                    pliststart = 0
                    plistsize = 100
                    self.logger.info("Breaking down processed into chunks of %d processed", plistsize)
                    while True:
                        if pliststart > len(processed_list):
                            break
                        response = self.maple_api.processed_post_many(
                            processed_list[pliststart:(pliststart+plistsize)])
                        if response is True:
                            self.logger.debug('Successfully sent processed from %d to %d', pliststart, pliststart+plistsize)
                            pliststart+= plistsize
                        elif isinstance(response, Response):
                            self.logger.error('Failed to post processed. Reattempting. %s', response)
                            
                self.logger.debug("Time to post processed: %.2fs", timeit.default_timer()-tstart_post)
                self._model_iteration.article_classified += len(processed_list)
                self._update_model_iteration(keep_fields=['article_classified'])
                
                # store articles and processed
                for var in ['_article_classified']:
                    if not hasattr(self, var):
                        setattr(self, var, [])

                tstart_extend = timeit.default_timer()
                getattr(
                    self,
                    '_article_classified'
                ).extend(articles)
                self.logger.debug("Time for extending articles: %.2fs",timeit.default_timer()-tstart_extend)
            
                
            except Exception as exc:
                self.logger.error('Failed to post processed. %s', exc)

            self.logger.info(
                'Classification cycle for %d articles was %f seconds. %d articles classified.',
                len(articles),
                timeit.default_timer()-time_start,
                self._model_iteration.article_classified)

            if self._debug_limits:
                if self._model_iteration.article_classified >= self.DEBUG_LIMIT_PROCESS_COUNT:
                    break
        
        # retrieve all processed.
        setattr(self, '_processed', self.retrieve_processed())
        # for level in range(1, 4):
        #     getattr(self._model_iteration,
        #             f'model_level{level}').status = 'complete'
        self._update_model_iteration(keep_fields=['article_classified'])

    # def _classify_articles(self, articles: list[Article], create_processed: bool = True):
    #     pass
    def retrieve_processed(self):
        processed = []
        request_size=1000
        skip = 0
        try:
            while True:
                response = self.maple_api.processed_get(
                    model_iteration_uuid=self._model_iteration.uuid,
                    limit=request_size,
                    skip=skip,
                    as_json=True)
                if isinstance(response, requests.Response):
                    self.logger.warning('Failed to retrieve processed. limit: %d, skip: %d', request_size, skip)
                else:
                    if len(response) == 0:
                        break
                    else:
                        skip+=request_size
                        processed.extend(response)
        except Exception as exc:
            self.logger.error("Failed to retrieve processed. %s", exc)
        self.logger.debug('Retrieved %d processed from backend.', len(processed))
        return processed
        
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

            model_structure = self._update_model_structure(
                level,
                model_structure=model_structure,
                keep_fields=['status'])

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
            # model_structure = self._update_model_structure(level=level, model_structure=model_structure)

            model_path = os.path.join(
                self._model_iteration_datapath,
                self._model_iteration.uuid,
                f'model_level{level}')
            os.makedirs(model_path, exist_ok=True)
            model.maple_save(model_path=model_path)
            
        # update model iteration on backend
        self._model_iteration.article_trained = len(documents)

        # TODO try catch
        while True:
            try:
                self._update_model_iteration(keep_fields=['article_trained'])
                break
            except Exception as exc:
                self.logger.warning('Failed to update model iteration. Reattempting... %s', exc)

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
                self.logger.debug('Wait for %.2f seconds', wait_time)
        
        
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
                time.sleep(random.random()*2)
            else:
                break
        
        while True:
            missing_keys = check_missing_keys(topic_mapping.keys(), get_topic_bullet_mapping().keys())
            if  len(missing_keys) != 0:
                self.logger.warning('Still missing requests for topic name from chatgpt for topic uuids: %s', missing_keys)
                time.sleep(random.random()*2)
            else:
                break
        
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
        if model.model_structure.topic is not None:
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
                    # self._update_model_structure(level=level, model_structure=model.model_structure)
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
                    # self._update_model_structure(level=level, model_structure=model.model_structure)
                    break
                else:
                    self.logger.warning("Failed updating topic. Reattempting... %s", updated_topic)
        
        return topic
    
    def _update_model_structure(
        self,
        level: int,
        model_structure: Model,
        keep_fields: list[str] = None):
        while True:
            updated_model_structure = self.maple_api.model_put(model_structure)
            if isinstance(updated_model_structure, Model):
                if keep_fields is not None:
                    for key in keep_fields:
                        setattr(model_structure, key, getattr(updated_model_structure, key))
                else:
                    model_structure = updated_model_structure
                break
            else:
                self.logger.warning(
                    'Failed to update model structure. %s', 
                    updated_model_structure)
                wait_time = random.random()*2
                self.logger.debug("Reattempt in %.2f seconds", wait_time)
                time.sleep(wait_time)
                continue
            
        setattr(self._model_iteration, f"model_level{level}", model_structure)
        setattr(
            getattr(self, f"model_level{level}"),
            'model_structure',
            model_structure
        )
        return getattr(self._model_iteration, f"model_level{level}")
        
    def _update_model_iteration(self, keep_fields: list[str]=None):
        """Updates the model iteration in the backend.

        Raises:
            AttributeError: _description_
            TypeError: _description_
        """
        tstart = timeit.default_timer()
        if not hasattr(self, '_model_iteration'):
            raise AttributeError("Missing _model_iteration attribute.")
        
        updated_model_structure = self.maple_api.model_iteration_put(
            self._model_iteration,
            keep_fields=keep_fields)
        self.logger.debug("Time to put model iteration: %.2fs", timeit.default_timer()-tstart)
        if not isinstance(updated_model_structure, ModelIteration):
            raise TypeError('Failed to update model structure')
        else:
            if keep_fields is None:
                self._model_iteration = updated_model_structure
            else:
                for key in keep_fields:
                    setattr(self._model_iteration,
                            key,
                            getattr(updated_model_structure, key))
            self.model_level1.model_structure = self._model_iteration.model_level1
            self.model_level2.model_structure = self._model_iteration.model_level2
            self.model_level3.model_structure = self._model_iteration.model_level3
        self.logger.debug(
            "Time to update model iteration: %.2fs (%s)",
            timeit.default_timer()-tstart,
            self._model_iteration.uuid)
        
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
                    content = article.chat_summary,
                    createDate = article.createDate,
                )
            )
        
        
        os.makedirs(self.model_iteration_path, exist_ok=True)
        
        to_store = [
            dict(value=article_out, name='article.json'),
            dict(value=self._processed, name='processed.json'),
            dict(value=self._model_iteration.to_dict(), name='model_iteration.json'),
        ]
        for var_to_store in to_store:
            try:
                with open(os.path.join(self.model_iteration_path, var_to_store['name']), 'w', encoding='utf-8') as file:
                    json.dump(var_to_store['value'], file, indent=2)
            except Exception as exc:
                self.logger.error('Failed to store file %s. %s', var_to_store['name'], exc)
        
        # zip directory now.
        shutil.make_archive(self.model_iteration_path, 'zip', self.model_iteration_path)

        self.remove_model_iteration_directory()
    
    def _create_chart_data(self):
        tstart = timeit.default_timer()
        articles = []
        for article in self._article_classified:
            articles.append(dict(
                uuid= article.uuid,
                url = article.url,
                createDate= article.createDate,
                content=article.chat_summary,
            ))
        
        
        topic_map = dict()
        topic_level_map = dict()
        for level in range(1,4):
            model = getattr(self, f'model_level{level}')
            for topic in model.model_structure.topic:
                topic_map[topic.uuid] = topic
                topic_level_map[topic.uuid] = level
        
        tstart_rtpt = timeit.default_timer()
        rtpt = RTPTResearch(
            processed = deepcopy(self._processed),
            article = articles,
            model_iteration = self._model_iteration.to_dict(),
            model_level1 = None,
            model_level2 = None,
            model_level3 = None,
        )
        
        self.logger.debug("Time to update load rtpt research from chart: %.2fs",
                            timeit.default_timer()-tstart_rtpt)
        
        for topic_uuid, chart in rtpt.charts.items():
            tstart_topic_update = timeit.default_timer()
            if topic_uuid in topic_map:
                topic = topic_map[topic_uuid]
                level = topic_level_map[topic_uuid]
                topic.chart.update(chart)
                self._update_topic_structure(level=level, topic=topic)
                self.logger.debug("Time to update topic from chart: %.2fs",
                                  timeit.default_timer()-tstart_topic_update)
            else:
                self.logger.warning('Missing topic uuid for chart')
        
        self.logger.debug("Time to update all charts: %.2fs",
                            timeit.default_timer()-tstart)
        
    def _on_model_iteration_fail(self):
        if hasattr(self, '_model_iteration'):
            if self._model_iteration.uuid is not None:
                try:
                    self.remove_model_iteration_directory()
                except Exception as exc:
                    self.logger.error("Failed to remove model directory. %s", exc )
                response = self.maple_api.model_iteration_delete(self._model_iteration.uuid)
                while response not in [200,]:
                    if response == 200:
                        self.logger.info ("Deleted model iteration %s in the backend.", self._model_iteration.uuid)
                    else:
                        self.logger.critical(
                            "Failed to delete model iteration %s in the backend. Response: %d.",
                            self._model_iteration.uuid,
                            response)
                        response = self.maple_api.model_iteration_delete(self.model_iteration_path.uuid)
                
        self._cleanup()
        
    def remove_model_iteration_directory(self):
        # remove original directory
        shutil.rmtree(self.model_iteration_path, ignore_errors=True)

    def _cleanup(self):
        self._chatgpt_client.sent_jobs = dict()
        self._chatgpt_client.topic_bullet_summary_results = []
        self._chatgpt_client.topic_name_results = []
        
    def run(self, *, run_once: bool = False):
        run_count = 0
        while True:
            try:
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
                    
                    #TODO create plot data for topics and models
                    self._create_chart_data()
                    # Set status of model_iteration to complete.
                    for level in range(1, 4):
                        model_structure = getattr(self._model_iteration,
                                f'model_level{level}')
                        model_structure.status = 'complete'
                        self._update_model_structure(
                            level=level,
                            model_structure=model_structure,
                            keep_fields=['status'])
                    # self._update_model_iteration(keep_fields=['status'])
                    
                    self._store_data()
                    
                    self._cleanup()
                    
                iteration_time = timeit.default_timer()-iteration_time_start
                self.logger.info(
                    'Iteration for %s ended in %.2f seconds',
                    self._model_iteration.name,
                    iteration_time)
            except Exception as exc:
                self.logger.critical('Failed model iteration. %s on line %d', exc, exc.__traceback__.tb_lineno)
                self._on_model_iteration_fail()
