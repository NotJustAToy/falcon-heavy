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

import typing as ty

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType
from .header import HeaderObject, HeaderObjectType
from .media_type import MediaTypeObject, MediaTypeObjectType
from .link import LinkObject, LinkObjectType
from .validators import CONTENT_TYPE_VALIDATOR

__all__ = (
    'ResponseObject',
    'ResponseObjectType',
)


class ResponseObject(t.Object):

    def __init__(self, path: ty.Optional[t.Path] = None, **kwargs: ty.Any) -> None:
        super(ResponseObject, self).__init__(**kwargs)
        self.path = path

    @property
    def description(self) -> str:
        return self['description']

    @property
    def headers(self) -> ty.Optional[ty.Mapping[str, HeaderObject]]:
        return self.get('headers')

    @property
    def content(self) -> ty.Optional[ty.Mapping[str, MediaTypeObject]]:
        return self.get('content')

    @property
    def links(self) -> ty.Optional[ty.Mapping[str, LinkObject]]:
        return self.get('links')


class ResponseObjectType(BaseOpenAPIObjectType[ResponseObject], result_class=ResponseObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'description': t.StringType(),
        'headers': t.MapType[HeaderObject](t.ReferenceType[HeaderObject](HeaderObjectType())),
        'content': t.MapType[MediaTypeObject](MediaTypeObjectType(), validators=(CONTENT_TYPE_VALIDATOR,)),
        'links': t.MapType[LinkObject](t.ReferenceType[LinkObject](LinkObjectType()))
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'description'
    }

    def convert(
            self, value: ty.Mapping, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[ResponseObject]:
        result: ty.Optional[ResponseObject] = super(ResponseObjectType, self).convert(value, path, **context)

        if result is None:
            return None

        result.path = path
        return result
