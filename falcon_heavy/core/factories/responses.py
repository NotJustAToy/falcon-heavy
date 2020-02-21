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

from falcon_heavy.core import types as t, openapi as o, make_response_conversion_context

from .common import SingleEntryMapType, ResponseCodeBestMatchedType
from .type import TypeFactory
from .content import ContentFactory
from .media_type import ResponseMediaTypeFactory
from .parameters import ParameterFactory
from .headers import HeadersFactory
from .response import ResponseObject, ResponseFactory

__all__ = (
    'ResponseConverter',
    'ResponsesFactory',
)


class ResponseConverter:

    __slots__ = ('subtype', )

    def __init__(self, subtype: ResponseCodeBestMatchedType[ResponseObject]):
        self.subtype = subtype

    def convert(
            self,
            status_code: int,
            headers: ty.Mapping[str, ty.Any],
            content: ty.Any = t.Undefined,
            content_type: ty.Optional[str] = None
    ) -> ty.Optional[ResponseObject]:
        if content_type is not None and content is not t.Undefined:
            data = {
                status_code: {
                    'content': {content_type: content},
                    'headers': headers
                }
            }
        else:
            data = {
                status_code: {
                    'headers': headers
                }
            }

        return self.subtype.convert(data, t.Path(), **make_response_conversion_context())


class ResponsesFactory:

    def __init__(self, type_factory: TypeFactory) -> None:
        self.type_factory = type_factory
        self.media_type_factory = ResponseMediaTypeFactory(self.type_factory)
        self.content_factory = ContentFactory(self.media_type_factory)
        self.parameter_factory = ParameterFactory(self.type_factory)
        self.headers_factory = HeadersFactory(self.parameter_factory)
        self.response_factory = ResponseFactory(self.content_factory, self.headers_factory)

    def generate(self, responses: ty.Mapping[str, o.ResponseObject]) -> ResponseConverter:
        return ResponseConverter(ResponseCodeBestMatchedType[ResponseObject](SingleEntryMapType[ResponseObject](), {
            status_code: self.response_factory.generate(response)
            for status_code, response in responses.items()
        }))
