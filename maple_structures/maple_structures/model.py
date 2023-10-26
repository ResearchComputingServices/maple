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

    def __init__(self) -> None:
        # super().__init__()
        for property in self.properties:
            setattr(self, property.name, property.default)

    """Base class used by structures in this file."""
    @property
    @abstractmethod
    def properties(self) -> [dict]:
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self):
        """Converts the object to dictionary"""
        out = dict()
        for property in self.properties:
            if getattr(self, property.name) is not None:
                if property.type == list:
                    out[property.name] = []
                    for item in getattr(self, property.name):
                        if hasattr(item, 'to_dict'):
                            out[property.name].append(item.to_dict())
                        else:
                            out[property.name].append(item)
                else:
                    out[property.name] = getattr(self, property.name)
            else:
                if property.include_if_none:
                    out[property.name] = getattr(self, property.name)

        return out

    # @staticmethod
    @abstractmethod
    @classmethod
    def from_dict(cls, data: dict):
        """Populates the class using data"""
        data_ = data.copy()
        for property in cls.properties():
            print(property)
        raise NotImplementedError()


class Model(Base):
    pass


class Dummy:
    def to_dict(self):
        return {}


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
        Property('model', type=Model, default=None)
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
                 model: Model = None):
        loc = locals()
        super().__init__()
        for var in ['name', 'keyword', 'label', 'dot_summary', 'prevalence', 'center', 'wordcloud', 'chart', 'model']:
            if loc[var] is not None:
                setattr(self, var, loc[var])

    @property
    def properties(self):
        return self._properties

    def to_dict(self):
        '''Converts Topic to dictionary'''
        return super().to_dict()

    @staticmethod
    def from_dict(data: dict):
        return super().from_dict(data)


if __name__ == "__main__":
    topic = Topic(name='Roger', dot_summary=['blash', 'teste'])
    print(json.dumps(topic.to_dict(), indent=2))
    # topic2 = Topic.from_dict(topic.to_dict)
    # print(json.dumps(topic2.to_dict(), indent=2))
    pass
