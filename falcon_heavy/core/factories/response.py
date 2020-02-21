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

from falcon_heavy.core import types as t, openapi as o

from .registry import registered, hashkey
from .content import ContentFactory
from .headers import HeadersFactory

__all__ = (
    'ResponseObject',
    'ResponseFactory',
)


class ResponseObject(t.Object):

    @property
    def content(self) -> ty.Optional[ty.Any]:
        return self.get('content', t.Undefined)

    @property
    def headers(self) -> ty.Mapping[str, str]:
        return self['headers']


class ResponseObjectType(t.ObjectType[ResponseObject], result_class=ResponseObject):

    __slots__ = ()


class EmptyResponseBodyType(t.AbstractConvertible):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'not_empty': "Expected empty response body"
    }

    __slots__ = ()

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        if value is not t.Undefined:
            raise t.SchemaError(t.Error(path, self.messages['not_empty']))

        raise t.UndefinedResultError()


class ResponseFactory:

    def __init__(self, content_factory: ContentFactory, headers_factory: HeadersFactory) -> None:
        self.content_factory = content_factory
        self.headers_factory = headers_factory

    @registered(key=lambda response: hashkey(response.path))
    def generate(self, response: o.ResponseObject) -> t.ObjectType:
        content = response.content

        return ResponseObjectType(
            properties={
                'content': EmptyResponseBodyType() if content is None else self.content_factory.generate(content),
                'headers': self.headers_factory.generate(response.headers)
            },
            additional_properties=False
        )
