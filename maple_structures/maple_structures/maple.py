'''Maple structures.
'''

from abc import ABC, abstractmethod
import json
from json.decoder import JSONDecodeError
import logging
import validators

logger = logging.getLogger("__maple__")


def _default_property(
    property_name, property_type, default_value, secondary_type=None, validator=None
):
    @property
    def prop(self):
        return getattr(self, f"_{property_name}", default_value)

    @prop.setter
    def prop(self, value):
        if value is None:
            return
        if not isinstance(value, property_type):
            raise TypeError(
                f"{property_name} should be a {property_type} but {type(value)} was provided."
            )
        if secondary_type is not None and isinstance(
            getattr(self, property_name), list
        ):
            for val in value:
                if not isinstance(val, secondary_type):
                    try:
                        val = secondary_type.from_json(val)
                    except Exception as exception:
                        raise exception
                        # raise TypeError(
                        #     f"Invalid secondary type {type(val)}. Should be {type(secondary_type)}"
                        # )
                if validator is not None:
                    if not validator(val):
                        raise ValueError(f"'{value}' did not pass validator.")
        else:
            if validator is not None:
                if not validator(value):
                    raise ValueError(f"'value' did not pass validator.")
        setattr(self, f"_{property_name}", value)

    return prop


class Base(ABC):
    '''Base class for Maple objects.'''

    def __init__(self) -> None:
        super().__init__()
        # self._validate_default_keys()

    # def _validate_default_keys(self):
    #     '''Validate default keys'''
    #     _default = self.default_keys()
    #     if not isinstance(_default, list):
    #         raise TypeError("'default_keys' method should return a 'list'.")

    @classmethod
    def validate(cls, value):
        '''Validates if value is of class type otherwise return a ValidationFailure.'''
        if isinstance(value, cls):
            return True
        else:
            return validators.ValidationFailure(func=cls.__name__, args={})

    @property
    @abstractmethod
    def default_keys(self):
        raise NotImplementedError()

    def _to_dict_endpoint(self):
        out = {}

        for key in self.default_keys():
            out[key] = getattr(self, key)

        invalid_keys = list(self.default_keys()) + [
            f"_{key}" for key in self.default_keys()
        ]

        out["metadata"] = dict()
        for key in self.__dict__.keys():
            if key not in invalid_keys:
                out["metadata"][key] = getattr(self, key)
        return out


class Author(Base):
    ''' Holds the Author information.'''
    _default_keys = ["name", "url", "email", "about"]

    def __init__(
        self,
        *,
        name: str = None,
        url: str = None,
        email: str = None,
        about: str = None,
        **kwargs,
    ):
        super().__init__()
        loc = locals()

        for key in self._default_keys:
            if key in loc.keys():
                if loc[key] is not None:
                    setattr(self, key, loc[key])

        for key in kwargs:
            if key not in self._default_keys:
                setattr(self, key, kwargs[key])

    def default_keys(self):
        return self._default_keys

    # def default_fields(self):
    #     return dict(
    #         name = dict(type=str,default=)
    #     )
    @property
    def name(self):
        return getattr(self, "_name", "")

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TypeError(f"name should be a string, not a {type(value)}")
        setattr(self, "_name", value)

    @property
    def url(self):
        return getattr(self, "_url", "")

    @url.setter
    def url(self, value):
        if value != '':
            if not validators.url(value):
                raise ValueError(f"'{value}'is not a valid url.")
        setattr(self, "_url", value)

    @property
    def email(self):
        return getattr(self, "_email", "")

    @email.setter
    def email(self, value):
        if value != '':
            if not validators.email(value):
                raise ValueError("Invalid email address.")
        setattr(self, "_email", value)

    @property
    def about(self):
        return getattr(self, "_about", "")

    @about.setter
    def about(self, value):
        if not isinstance(value, str):
            raise TypeError("'about; should be a string.")
        setattr(self, "_about", value)

    def to_dict(self):
        author = self._to_dict_endpoint()
        if author['email'] == '':
            author.pop('email')
        return author

    @staticmethod
    def from_json(data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except JSONDecodeError as exc:
                logger.error(f"Author.from_json: {exc}")
                raise TypeError("data was not a valid json formatted string")
        try:
            author = Author(**data)
            return author
        except Exception as e:
            logger.debug(f"Author.from_json: {e}")
            raise ValueError(f"Could not create author from json. {e}")


class Comments(Base):
    _default_keys = ["title", "author"]
    # TODO content, likes, shares, reply_content, comment_id

    def __init__(self) -> None:
        super.__init__()

    def default_keys(self):
        return self._default_keys

    @property
    def title(self):
        return getattr(self, "_title", "")

    @title.setter
    def title(self, value):
        if not isinstance(value, str):
            raise TypeError(
                f"title should be a string, but '{type(value)}' was provided."
            )
        setattr(self, "_title", value)

    @property
    def author(self):
        return getattr(self, "_author", [])

    @author.setter
    def author(self, value):
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, list):
            for val in value:
                # TODO
                pass

    @staticmethod
    def from_json(data):
        '''from json'''
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Json as exc:
                raise ValueError(f"Invalid json format. {data}")
        comment = Comments()
        for key in data.keys():
            try:
                setattr(comment, key, data[key])
            except:
                logger.debug(
                    f"Comments:from_json: Invalid data: '{key}':{data[key]}")
        return comment

    def to_dict(self):
        return self._to_dict_endpoint()


_article_properties = [
    dict(name='uuid', type=str, default=None),
    dict(name="url", type=str, default="", validator=validators.url),
    dict(name="title", type=str, default=""),
    dict(name="summary", type=str, default=""),
    dict(name="content", type=str, default=""),
    dict(name="author", type=list, default=[],
         secondary_type=Author, validator=Author.validate),
    dict(name="video_url", type=list, default=[],
         secondary_type=str, validator=validators.url),
    dict(name="date_published", type=str, default=None),
    dict(name="date_modified", type=str, default=None),
    dict(name="createDate", type=str, default=None),
    dict(name="modifyDate", type=str, default=None),
    dict(name="number_of_likes", type=int, default=0),
    dict(name="number_of_shares", type=int, default=0),
    dict(name="comments", type=list, default=[], secondary_type=Comments),
    # dict(name="topic", type=list, secondary_type=str, default=[]),
    dict(name="language", type=str, default=""),
    dict(name="source", type=str, default=None),
    dict(name="geographic_location", type=str, default=None),
    dict(name="location_name", type=str, default=None),
    dict(name="metadata", type=dict, default={}),
]


class Article(Base):
    '''Article'''
    _properties = _article_properties.copy()

    _suppress_errors = False

    def __init__(self):
        super().__init__()
        setattr(self, "_author", [])
        for prop in self._properties:
            setattr(
                Article,
                prop["name"],
                _default_property(
                    prop["name"],
                    prop["type"],
                    prop["default"],
                    secondary_type=None
                    if "secondary_type" not in prop.keys()
                    else prop["secondary_type"],
                    validator=None
                    if "validator" not in prop.keys()
                    else prop["validator"],
                ),
            )

    @property
    def default_keys(self):
        return getattr(self, '_default_keys', [])

    def add_author(self, author: Author):
        '''add author to article'''
        if not isinstance(author, Author):
            raise TypeError(
                f"'author' should be of type {type(Author)}, not type {type(author)}"
            )
        if getattr(self, '_author', []) is None:
            setattr(self, '_author', [])
        authors = getattr(self, '_author', [])
        authors.append(author)
        setattr(self, '_author', authors)

    def to_dict(self, *, suppress_null=True):
        '''converts Article to dictionary'''
        out = dict()
        for prop in self._properties:
            attr = getattr(self, prop["name"])
            if suppress_null:
                if attr is None:
                    continue
            if isinstance(attr, list):
                outlist = []
                for val in attr:
                    try:
                        outlist.append(val.to_dict())
                    except AttributeError:
                        outlist.append(val)
                out[prop["name"]] = outlist
            else:
                if hasattr(prop['type'], 'to_dict'):
                    out[prop["name"]] = attr.to_dict()
                else:
                    out[prop["name"]] = attr

        for key in self.__dict__.keys():
            if key[1:] not in out.keys():
                out["metadata"][key] = getattr(self, key)

        return out

    @staticmethod
    def from_json(data, *, mapping=None):
        '''constructs an article provided the json'''
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                raise ValueError(f"Invalid json format. {data}")

        # mapping keywords fom a different structure
        if mapping is not None:
            converted = dict()

            for key in data.keys():
                if key in mapping.keys():
                    converted[mapping[key]] = data.pop(key)

            if any(key in data.keys() for key in converted):
                raise ValueError('Mapped key already exist in data')

            data.update(converted)

        article = Article()

        properties = {}
        for property in article._properties:
            name = property.copy().pop("name")
            properties[name] = property

        for key in data.keys():
            if key in properties.keys():
                if key == 'metadata':
                    invalid_metadata_keys = ['_author']
                    for metadata_key in data[key]:
                        if metadata_key not in invalid_metadata_keys:
                            setattr(article, metadata_key,
                                    data[key][metadata_key])
                else:
                    if properties[key]["type"] is list:
                        outlist = []
                        if isinstance(data[key], list):
                            for item in data[key]:
                                try:
                                    outlist.append(
                                        properties[key]["secondary_type"].from_json(
                                            item)
                                    )
                                except:
                                    outlist.append(item)
                        setattr(article, key, outlist)
                    else:
                        if hasattr(properties[key]["type"], 'from_json'):
                            setattr(
                                article, key, properties[key]["type"].from_json(data[key]))
                        else:
                            setattr(article, key, data[key])
            else:
                setattr(article, key, data[key])
        return article

    @classmethod
    def from_dict(cls, data):
        return cls.from_json(data)
