from abc import ABC, abstractmethod
import json


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
        return {prop.name:prop for prop in self.properties}

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
                if hasattr(getattr(self, prop.name),'to_dict'):
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
                            raise TypeError(f"{prop_name} should be of type {prop.type}")
                        for data_item in data_[prop_name]:
                            if hasattr(prop.secondary_type, 'from_dict'):
                                getattr(obj, prop_name).append(prop.secondary_type.from_dict(data_item))
                            else:
                                getattr(obj, prop_name).append(data_item)
                    elif hasattr(prop.type, 'from_dict'):
                        setattr(obj, prop_name, prop.type.from_dict(data[prop_name]))
                    else:
                        setattr(obj, prop_name, data[prop_name])
                
        return obj
            

    # @abstractmethod
    def to_json(self):
        return json.dumps(self.to_dict())


class Topic(Base):  # We have to replace it with the topic base
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
        self._properties.append(Property('model', type=globals()['Model'], default=None))
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
        exclude = [prop for prop in self.properties if prop.name=='topic']
        out =  super().to_dict(exclude=exclude)
        if include_topic:
            topics = getattr(self, 'topic')
            if topics is not None:
                out['topic']=[]
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
                getattr(out,'topic').append(Topic.from_dict(topic))
        return out
    
    def add_topic(self, topic: Topic):
        if getattr(self, 'topic', None) is None:
            setattr(self,'topic', [])
        getattr(self,'topic').append(topic)


if __name__ == "__main__":
    topic = Topic(name='Topic1', dot_summary=['topic 1 is awesome', 'Completely related to something.'])
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

    pass
