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

from falcon_heavy.core import types as t, openapi as o

from .registry import registered, hashkey
from .content import ContentFactory

__all__ = (
    'RequestBodyType',
    'RequestBodyFactory',
)


class RequestBodyType(t.AbstractConvertible):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'required': "Request body is required"
    }

    __slots__ = ('subtype', 'required')

    def __init__(self, subtype: t.AbstractConvertible, required: bool = False, **kwargs: ty.Any) -> None:
        super(RequestBodyType, self).__init__(**kwargs)
        self.subtype = subtype
        self.required = required

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        if value is t.Undefined and self.required:
            raise t.SchemaError(t.Error(path, self.messages['required']))

        return self.subtype.convert(value, path, *args, **context)


class RequestBodyFactory:

    def __init__(self, content_factory: ContentFactory) -> None:
        self.content_factory = content_factory

    @registered(key=lambda request_body: hashkey(request_body.path))
    def generate(self, request_body: o.RequestBodyObject) -> RequestBodyType:
        return RequestBodyType(self.content_factory.generate(request_body.content), required=request_body.required)
