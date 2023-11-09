from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod
import json
import pprint
from .maple import Article


class Property:
    """Property used by underlying structures.
    """

    def __init__(self,
                 name: str,
                 type: any,
                 default: any,
                 secondary_type: any = None,
                 include_if_none: bool = False) -> None:
        self.name = name
        self.type = type
        self.default = default
        self.secondary_type = secondary_type
        self.include_if_none = include_if_none


class Base(ABC):
    """Base class used by structures in this file.
    """
    _properties = []

    def __init__(self) -> None:
        # super().__init__()
        for prop in self.properties:
            setattr(self, prop.name, prop.default)

    @property
    @abstractmethod
    def properties(self) -> [Property]:
        raise NotImplementedError()

    @property
    def properties_dict(self):
        return {prop.name: prop for prop in self.properties}

    @abstractmethod
    def to_dict(self, *, exclude: list[Property] = None):
        """Converts the object to dictionary"""
        out = dict()
        for prop in self.properties:
            if exclude is not None:
                if prop in exclude:
                    continue
            if getattr(self, prop.name) is not None:
                if prop.type == list:
                    out[prop.name] = []
                    for item in getattr(self, prop.name):
                        if hasattr(item, 'to_dict'):
                            out[prop.name].append(item.to_dict())
                        else:
                            out[prop.name].append(item)
                if hasattr(getattr(self, prop.name), 'to_dict'):
                    out[prop.name] = getattr(self, prop.name).to_dict()
                else:
                    out[prop.name] = getattr(self, prop.name)
            else:
                if prop.include_if_none:
                    out[prop.name] = getattr(self, prop.name)

        return out

    # @classmethod
    def _from_dict(cls, data: dict):
        """Populates the class using data"""
        data_ = data.copy()
        props = {prop.name: prop for prop in cls._properties}
        # prop_keys = [prop.name for prop in cls._properties]
        obj = cls()
        for item in props.items():
            prop_name, prop = item
            if prop_name in data:
                if data_[prop_name] is not None:
                    if prop.type == list:
                        setattr(obj, prop_name, [])
                        if not isinstance(data_[prop_name], list):
                            raise TypeError(
                                f"{prop_name} should be of type {prop.type}")
                        for data_item in data_[prop_name]:
                            if hasattr(prop.secondary_type, 'from_dict'):
                                getattr(obj, prop_name).append(
                                    prop.secondary_type.from_dict(data_item))
                            else:
                                getattr(obj, prop_name).append(data_item)
                    elif hasattr(prop.type, 'from_dict'):
                        setattr(obj, prop_name,
                                prop.type.from_dict(data[prop_name]))
                    else:
                        setattr(obj, prop_name, data[prop_name])

        return obj

    # @abstractmethod

    def to_json(self):
        return json.dumps(self.to_dict())


class Topic(Base):
    '''Topic'''
    _properties = [
        Property('uuid', type=str, default=None),
        Property('createDate', type=str, default=None),
        Property('modifyDate', type=str, default=None),
        Property('name', type=str, default=None),
        Property('keyword', type=list, default=None),
        Property('label', type=str, default=None),
        Property('dot_summary', type=list,
                 default=None, secondary_type=str),
        Property('prevalence', type=float, default=None),
        Property('center', type=list, default=None, secondary_type=float),
        Property('wordcloud', type=dict, default=None),
        Property('chart', type=dict, default=None),
        # Property('model', type=globals()['Model'], default=None)
    ]

    def __init__(self, *,
                 name: str = None,
                 keyword: [str] = None,
                 label: str = None,
                 dot_summary: [str] = None,
                 prevalence: float = None,
                 center: [float] = None,
                 wordcloud: dict = None,
                 chart: dict = None,
                 model: 'Model' = None):
        self._properties.append(
            Property('model', type=globals()['Model'], default=None))
        loc = locals()
        super().__init__()
        for var in ['name', 'keyword', 'label', 'dot_summary', 'prevalence', 'center', 'wordcloud', 'chart', 'model']:
            if loc[var] is not None:
                setattr(self, var, loc[var])

    @property
    def properties(self):
        return self._properties

    def to_dict(self, *, include_model: bool = False):
        '''Converts Topic to dictionary'''
        exclude = [prop for prop in self.properties if prop.name == 'model']
        out = super().to_dict(exclude=exclude)
        if include_model:
            if hasattr(self, 'model'):
                out['model'] = self.model.to_dict()
        return out

    @classmethod
    def from_dict(cls, data: dict):
        return super()._from_dict(cls, data)


class Model(Base):
    '''Model'''
    _properties = [
        Property('uuid', type=str, default=None),
        Property('createDate', type=str, default=None),
        Property('modifyDate', type=str, default=None),
        Property('type', type=str, default=None),
        Property('version', type=str, default=None),
        Property('name', type=str, default=None),
        Property('status', type=str, default=None),
        Property('level', type=int, default=1),
        Property('path', type=str, default=None),
        Property('topic', type=list, default=None, secondary_type=Topic)
    ]

    def __init__(self, *,
                 type: str = None,
                 version: str = None,
                 name: str = None,
                 status: str = None,
                 level: int = None,
                 path: str = None,
                 # topic: [Topic] = None):
                 topic: [] = None):
        loc = locals()
        super().__init__()
        for var in ['type', 'version', 'name', 'status', 'level', 'path', 'topic']:
            if loc[var] is not None:
                setattr(self, var, loc[var])

    @property
    def properties(self):
        return self._properties

    def to_dict(self, *, include_topic: bool = False):
        '''Converts Model to dictionary'''
        exclude = [prop for prop in self.properties if prop.name == 'topic']
        out = super().to_dict(exclude=exclude)
        if include_topic:
            topics = getattr(self, 'topic')
            if topics is not None:
                out['topic'] = []
                for topic in topics:
                    out['topic'].append(
                        topic.to_dict(include_model=False)
                    )
        return out

    @classmethod
    def from_dict(cls, data: dict):
        out = super()._from_dict(cls, data)
        if 'topic' in data:
            setattr(out, 'topic', [])
            for topic in data['topic']:
                getattr(out, 'topic').append(Topic.from_dict(topic))
        return out

    def add_topic(self, topic: Topic):
        if getattr(self, 'topic', None) is None:
            setattr(self, 'topic', [])
        getattr(self, 'topic').append(topic)


class ModelIteration(Base):
    '''Model Iteration'''
    _properties = [
        Property('uuid', type=str, default=None),
        Property('createDate', type=str, default=None),
        Property('modifyDate', type=str, default=None),
        Property('name', type=str, default=None),
        Property('type', type=str, default=None),
        Property('model_level1', type=Model, default=None),
        Property('model_level2', type=Model, default=None),
        Property('model_level3', type=Model, default=None),
        Property('article_trained', type=int, default=0),
        Property('article_classified', type=int, default=0),
    ]

    def __init__(self, *,
                 name: str = None,
                 type: [str] = None,
                 model_level1: Model = None,
                 model_level2: Model = None,
                 model_level3: Model = None,
                 article_trained: int = 0,
                 article_classified: int = 0):
        loc = locals()
        super().__init__()
        for var in ['name', 'type', 'model_level1', 'model_level2', 'model_level3', 'article_trained', 'article_classified']:
            if loc[var] is not None:
                setattr(self, var, loc[var])

    @property
    def properties(self):
        return self._properties

    def to_dict(self, include_model: bool = True, include_topic: bool = True):
        '''Converts Model Iteration to dictionary'''
        out = super().to_dict()
        if include_model:
            if hasattr(self, 'model_level1'):
                if self.model_level1 is not None:
                    out['model_level1'] = self.model_level1.to_dict(
                        include_topic=include_topic)
            if hasattr(self, 'model_level2'):
                if self.model_level2 is not None:
                    out['model_level2'] = self.model_level2.to_dict(
                        include_topic=include_topic)
            if hasattr(self, 'model_level3'):
                if self.model_level3 is not None:
                    out['model_level3'] = self.model_level3.to_dict(
                        include_topic=include_topic)
        return out

    @classmethod
    def from_dict(cls, data: dict):
        out = super()._from_dict(cls, data)
        return out

    def add_model_level(self, level: str,  model: Model):
        valid_levels = [f'model_level{i}' for i in range(1, 4)]
        if level not in valid_levels:
            raise ValueError(
                'Invalid level: %s. Valid levels are: %s', level, valid_levels)
        setattr(self, level, model)


class Processed(Base):
    '''Model Iteration'''
    _properties = [
        Property('uuid', type=str, default=None),
        Property('createDate', type=str, default=None),
        Property('modifyDate', type=str, default=None),
        Property('article', type=Article, default=None),
        Property('modelIteration', type=ModelIteration, default=None),
        Property('topic_level1', type=Topic, default=None),
        Property('topic_level1_prob', type=float, default=None),
        Property('topic_level2', type=Topic, default=None),
        Property('topic_level2_prob', type=float, default=None),
        Property('topic_level3', type=Topic, default=None),
        Property('topic_level3_prob', type=float, default=None),
        Property('position', type=List[float], default=None),
    ]

    def __init__(
        self,
        article: Article = None,
        modelIteration: ModelIteration = None,
        topic_level1: Topic = None,
        topic_level1_prob: float = None,
        topic_level2: Topic = None,
        topic_level2_prob: float = None,
        topic_level3: Topic = None,
        topic_level3_prob: float = None,
        position: list[float] = None
    ) -> None:
        loc = locals()
        super().__init__()
        for var in [
            'article',
            'modelIteration',
            'topic_level1',
            'topic_level1_prob',
            'topic_level2',
            'topic_level2_prob',
            'topic_level3',
            'topic_level3_prob',
                'position']:
            if loc[var] is not None:
                setattr(self, var, loc[var])

    @property
    def properties(self):
        return self._properties

    def to_dict(self):
        # return super().to_dict()
        out = dict()
        for var in ['article', 'modelIteration', 'topic_level1', 'topic_level2', 'topic_level3']:
            var_obj = getattr(self, var, None)
            if not var_obj:
                raise AttributeError("missing attribute %s", var)
            if not getattr(var_obj, 'uuid', None):
                raise AttributeError("%s is lacking uuid", var)
            out[var] = dict(uuid=getattr(self, var).uuid)

        for level in range(1, 4):
            var_name = f'topic_level{level}_prob'
            var = getattr(self, var_name, None)
            if var:
                out[var_name] = var

        var_name = "position"
        var = getattr(self, var_name, None)
        if var:
            out[var_name] = var

        return out

    @classmethod
    def from_dict(cls, data: dict):
        return super()._from_dict(cls, data)


if __name__ == "__main__":
    old_testing = False
    if old_testing:
        topic = Topic(name='Topic1', dot_summary=[
            'topic 1 is awesome', 'Completely related to something.'])
        print('Topic:')
        print(json.dumps(topic.to_dict(), indent=2))

        topic2 = Topic.from_dict(topic.to_dict())
        print('Topic from_dict:')
        print(topic2.to_dict())

        model = Model(type='bert', level=1)

        print("Topic to_dict with model")
        topic2.model = model
        print(topic2.to_dict(include_model=True))

        model.add_topic(topic)
        model.add_topic(topic2)

        print("Model to_dict with topics:")
        print(model.to_dict(include_topic=True))
        model2 = Model.from_dict(model.to_dict(include_topic=True))

        print("model2 from_dict")
        print(model2.to_dict(include_topic=True))

        print("================================================ ")
        model1 = Model(type='bert', level=1)
        topic1 = Topic(name='GazaConflict', dot_summary=[
            'Conflict in Gaza', 'War crisis'])
        topic2 = Topic(name='HousingCrisis', dot_summary=[
            'Canda wide housing crisis', 'Rental and buying properties'])

        topic1.model = model1
        topic2.model = model1
        model1.add_topic(topic1)
        model1.add_topic(topic2)
        print(model1.to_dict(include_topic=True))

        model2 = Model(type='stm', level=1)
        topic3 = Topic(name='GazaConflict', dot_summary=[
            'Conflict in Gaza', 'War crisis'])
        topic4 = Topic(name='HousingCrisis', dot_summary=[
            'Canda wide housing crisis', 'Rental and buying properties'])

        topic3.model = model2
        topic4.model = model2
        model2.add_topic(topic3)
        model2.add_topic(topic4)

        print("================================================ ")
        # model_it1 = ModelIteration(name='it1', type='bert', model_level1=model1,
        #                           article_trained=2000, article_classified=1885)

        # model_it1 = ModelIteration(name='it1', type='bert', model_level1=model1,
        #                           model_level2=model2, article_trained=2000, article_classified=1885)

        # model_it1 = ModelIteration(name='it1', type='bert', model_level1=model1,
        #                           article_trained=2000, article_classified=1885)

        model_it1 = ModelIteration(
            name='it1', type='bert', article_trained=2000, article_classified=1885)

        print(model_it1.to_dict())

        print("======================================================")
        model_it1.add_model_level('model_level1', model1)
        model_it1.add_model_level('model_level2', model2)
        model_it1.add_model_level('model_level3', model1)

        # print(model_it1.to_dict(include_model=True, include_topic=True))
        pprint.pprint(model_it1.to_dict())

        # print("..............................................")
        # print(model_it1.to_dict_simple())

    t_article = Article(url="https://www.cbc.ca/news/canada/nova-scotia/group-neighbours-helping-homeless-encampment-1.7019732",
                        title="Neighbours help homeless",
                        content="Newly formed Gated Community Association started as a Facebook group and is now a registered non-profit.",
                        )
    t_topic1 = Topic(name='Topic1', dot_summary=[
                     'topic 1 is awesome', 'Completely related to something.'])
    t_model1 = Model(type='bert', level=1)
    t_topic1.model = t_model1
    t_model1.add_topic(t_topic1)
    t_model_it1 = ModelIteration(
        name='it1', type='bert', article_trained=2000, article_classified=1885)
    t_model_it1.add_model_level('model_level1', t_model1)
