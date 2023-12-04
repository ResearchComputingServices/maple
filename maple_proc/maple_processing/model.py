from abc import abstractmethod
import logging
import os
from maple_chatgpt.chatgpt_client import ChatgptClient
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
from sentence_transformers import SentenceTransformer

logging.getLogger('numba').setLevel(logging.WARNING)

class TopicInfo:
    def __init__(
        self,
        name: str = None,
        keyword: list[str] = None,
        label: str = None,
        index: int = None,
        prevalence: float = None,
        representative_docs: list[str] = None,
        ):
        self.name = name
        self.keyword = keyword
        self.label = label
        self.index = index
        self.prevalence = prevalence
        self.representative_docs = representative_docs
        

class MapleModel:
    def __init__(self,
                 model_type: str = None,
                 version: str = None,
                 name: str = None,
                 status: str = None,
                 level: int = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        existing_variables = []
        for var in ['type', 'version', 'name', 'status', 'level']:
            if hasattr(self, var):
                existing_variables.append(var)
        if len(existing_variables) > 0:
            raise ValueError(
                f'Variable already exist is supper: {existing_variables}')
        self.type = model_type or ''
        self.version = version or '1.0'
        self.name = name or ''
        self.status = status or 'created'
        self.level = level or 1
        self.logger = logging.getLogger(
            'maple' if name == '' else f'maple_{name}')
        self._verify_functions()

    @property
    def model_structure(self):
        """the model structure of the model that is used by the backend

        Returns:
            Model: structure with fields specified in backend.
        """
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

    @abstractmethod
    def maple_get_topic_info(self):
        raise NotImplementedError

    @abstractmethod
    def maple_save(self, model_path: str):
        raise NotImplementedError()
    

class MapleBert(MapleModel, BERTopic):
    
    logger = logging.getLogger("MapleBert")
    
    def __init__(self, **kwargs) -> None:
        super().__init__(model_type='bert',
                         version='1.0',
                         name='BERTopic',
                         status='created',
                         level=1,
                         **kwargs)

    @classmethod
    def create_model(cls, level: int, training_size: int = None):
        dbscan_kwargs = dict(
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True,
        )

        if level == 1:
            dbscan_kwargs['min_cluster_size'] = 150 if training_size is None else int(
                training_size/12*0.6)
        elif level == 2:
            dbscan_kwargs['min_cluster_size'] = 50 if training_size is None else int(
                training_size/35*0.6)
        elif level == 3:
            dbscan_kwargs['min_cluster_size'] = 10 if training_size is None else int(
                training_size/50*0.6)

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
            ngram_range=(1, 2))

        keybert_model = KeyBERTInspired()
        representation_model = {"KeyBERT": keybert_model}

        return cls(
            hdbscan_model=hdbscan_model,
            umap_model=umap_model,
            vectorizer_model=vectorizer_model,
            representation_model=representation_model,
        )

    def maple_get_topic_info(self, documents_len: int = None) -> list[TopicInfo]:
        """Should return a list of TopicInfo.

        Returns:
            list[TopicInfo]: a list with variables needed to manage topics.
        """
        out = []
        topic_info = self.get_topic_info()
        documents_len = topic_info['Topic'].sum()
        for row in topic_info.iterrows():
            out.append(
                TopicInfo(
                    name=row[1]['Name'],
                    keyword=row[1]['Representation'],
                    label='',
                    index=row[1]['Topic'],
                    prevalence=self.topic_sizes_[row[1]['Topic']] / documents_len,
                    representative_docs=row[1].Representative_Docs,
                ),
            )
        return out

    def maple_save(self, model_path: str):
        os.makedirs(model_path, exist_ok=True)
        self.save(
            path = model_path,
            serialization="pytorch",
            save_ctfidf=True,
            save_embedding_model=self.embedding_model,
        )
        

