# Copyright 2019-2020 Not Just A Toy Corp.
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
from .media_type import MediaTypeObject, MediaTypeObjectType
from .validators import CONTENT_TYPE_VALIDATOR

__all__ = (
    'RequestBodyObject',
    'RequestBodyObjectType',
)


class RequestBodyObject(t.Object):

    def __init__(self, path: ty.Optional[t.Path] = None, **kwargs: ty.Any) -> None:
        super(RequestBodyObject, self).__init__(**kwargs)
        self.path = path

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def content(self) -> ty.Mapping[str, MediaTypeObject]:
        return self['content']

    @property
    def required(self) -> bool:
        return self['required']


class RequestBodyObjectType(BaseOpenAPIObjectType[RequestBodyObject], result_class=RequestBodyObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'description': t.StringType(),
        'content': t.MapType[MediaTypeObject](MediaTypeObjectType(), validators=(CONTENT_TYPE_VALIDATOR,)),
        'required': t.BooleanType(default=False)
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'content'
    }

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[RequestBodyObject]:
        result: ty.Optional[RequestBodyObject] = super(RequestBodyObjectType, self).convert(value, path, **context)

        if result is None:
            return None

        result.path = path
        return result
