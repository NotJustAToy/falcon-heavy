# Copyright 2019 Not Just A Toy Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import warnings
import typing as ty

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType
from .schema import SchemaObject, SchemaObjectType
from .example import ExampleObject, ExampleObjectType
from .validators import CONTENT_TYPE_VALIDATOR
from .constants import (
    PARAMETER_LOCATION,
    PARAMETER_STYLE
)

__all__ = (
    'BaseParameterObject',
    'BaseParameterObjectType',
    'NamedParameterObject',
    'NamedParameterObjectType',
    'LocatedParameterObject',
    'PathParameterObject',
    'PathParameterObjectType',
    'QueryParameterObject',
    'QueryParameterObjectType',
    'HeaderParameterObject',
    'HeaderParameterObjectType',
    'CookieParameterObject',
    'CookieParameterObjectType',
    'AnyParameterObject',
    'ParameterPolymorphic',
)


class BaseParameterObject(t.Object):

    def __init__(self, path: ty.Optional[t.Path] = None, **kwargs: ty.Any) -> None:
        super(BaseParameterObject, self).__init__(**kwargs)
        self.path = path

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def required(self) -> bool:
        return self['required']

    @property
    def deprecated(self) -> bool:
        return self['deprecated']

    @property
    def style(self) -> str:
        return self['style']

    @property
    def explode(self) -> bool:
        return self.get('explode', self.style == PARAMETER_STYLE.FORM)

    @property
    def allow_reserved(self) -> bool:
        return self['allowReserved']

    @property
    def schema(self) -> ty.Optional[SchemaObject]:
        return self.get('schema')

    @property
    def example(self) -> ty.Optional[ty.Any]:
        return self.get('example')

    @property
    def examples(self) -> ty.Optional[ty.Mapping[str, ExampleObject]]:
        return self.get('examples')

    @property
    def content(self) -> ty.Optional[ty.Tuple[str, 'MediaTypeObject']]:
        if 'content' in self:
            return next(iter(self['content'].items()))

        return None


T_base = ty.TypeVar('T_base', bound=BaseParameterObject)


class BaseParameterObjectType(BaseOpenAPIObjectType[T_base]):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'deprecated': "Parameter '{0}' is deprecated",
        'mutually_exclusive_schema_content_keywords': "The keywords `schema` and `content` are mutually exclusive"
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'description': t.StringType(),
        'required': t.BooleanType(default=False),
        'deprecated': t.BooleanType(default=False),
        'style': t.StringType(enum=PARAMETER_STYLE),
        'explode': t.BooleanType(),
        'allowReserved': t.BooleanType(
            enum=[False],
            messages={'enum': "`allowReserved` permanently unsupported"},
            default=False
        ),
        'schema': t.ReferenceType[SchemaObject](SchemaObjectType()),
        'example': t.AnyType(),
        'examples': t.MapType[ExampleObject](t.ReferenceType[ExampleObject](ExampleObjectType())),
        'content': t.MapType['MediaTypeObject'](
            value_type=t.LazyType['MediaTypeObject'](lambda: MediaTypeObjectType()),
            min_values=1,
            max_values=1,
            validators=(CONTENT_TYPE_VALIDATOR,)
        )
    }

    def convert(
            self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[T_base]:
        result: ty.Optional[T_base] = super(BaseParameterObjectType, self).convert(value, path, **context)

        if result is None:
            return result

        if result.deprecated:
            warnings.warn(self.messages['deprecated'].format(path), DeprecationWarning)

        result.path = path
        return result

    def validate_mutually_exclusive_schema_content_keywords(
            self, value: T_base, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if 'schema' in value and 'content' in value:
            return self.messages['mutually_exclusive_schema_content_keywords']

        return None


class NamedParameterObject(BaseParameterObject):

    @property
    def name(self) -> str:
        return self['name']


T_named = ty.TypeVar('T_named', bound=NamedParameterObject)


class NamedParameterObjectType(BaseParameterObjectType[T_named]):

    PROPERTIES: ty.ClassVar[t.Properties] = {  # type: ignore
        'name': t.StringType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'name'
    }


class LocatedParameterObject(NamedParameterObject):

    @property
    def location(self) -> str:
        return self['in']


class PathParameterObject(LocatedParameterObject):
    pass


class PathParameterObjectType(NamedParameterObjectType[PathParameterObject], result_class=PathParameterObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {  # type: ignore
        'in': t.StringType(enum=(PARAMETER_LOCATION.PATH,)),
        'required': t.BooleanType(
            enum=[True],
            messages={'enum': "For path parameter this property must be True"}
        ),
        'style': t.StringType(
            enum=(
                PARAMETER_STYLE.SIMPLE,
                PARAMETER_STYLE.LABEL,
                PARAMETER_STYLE.MATRIX
            ),
            default=PARAMETER_STYLE.SIMPLE
        )
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'in',
        'required'
    }


class QueryParameterObject(LocatedParameterObject):

    @property
    def allow_empty_value(self) -> bool:
        return self['allowEmptyValue']


class QueryParameterObjectType(NamedParameterObjectType[QueryParameterObject], result_class=QueryParameterObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {  # type: ignore
        'in': t.StringType(enum=(PARAMETER_LOCATION.QUERY,)),
        'allowEmptyValue': t.BooleanType(default=False),
        'style': t.StringType(
            enum=(
                PARAMETER_STYLE.FORM,
                PARAMETER_STYLE.SPACE_DELIMITED,
                PARAMETER_STYLE.PIPE_DELIMITED,
                PARAMETER_STYLE.DEEP_OBJECT
            ),
            default=PARAMETER_STYLE.FORM
        )
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'in'
    }


class HeaderParameterObject(LocatedParameterObject):
    pass


class HeaderParameterObjectType(NamedParameterObjectType[HeaderParameterObject], result_class=HeaderParameterObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {  # type: ignore
        'in': t.StringType(enum=(PARAMETER_LOCATION.HEADER,)),
        'style': t.StringType(enum=(PARAMETER_STYLE.SIMPLE,), default=PARAMETER_STYLE.SIMPLE)
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'in'
    }


class CookieParameterObject(LocatedParameterObject):
    pass


class CookieParameterObjectType(NamedParameterObjectType[CookieParameterObject], result_class=CookieParameterObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {  # type: ignore
        'in': t.StringType(enum=(PARAMETER_LOCATION.COOKIE,)),
        'style': t.StringType(enum=(PARAMETER_STYLE.FORM,), default=PARAMETER_STYLE.FORM)
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'in'
    }


AnyParameterObject = ty.Union[
    PathParameterObject,
    QueryParameterObject,
    HeaderParameterObject,
    CookieParameterObject
]


ParameterPolymorphic = t.DiscriminatedType(
    property_name='in',
    mapping={
        PARAMETER_LOCATION.PATH: PathParameterObjectType(),
        PARAMETER_LOCATION.QUERY: QueryParameterObjectType(),
        PARAMETER_LOCATION.HEADER: HeaderParameterObjectType(),
        PARAMETER_LOCATION.COOKIE: CookieParameterObjectType()
    }
)


from .media_type import MediaTypeObject, MediaTypeObjectType  # noqa
