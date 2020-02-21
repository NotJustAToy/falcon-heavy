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

from falcon_heavy.core import types as t, openapi as o, make_request_conversion_context

from .type import TypeFactory
from .parameters import ParameterFactory, ParametersFactory
from .headers import HeadersFactory
from .media_type import RequestMediaTypeFactory
from .content import ContentFactory
from .request_body import RequestBodyFactory

__all__ = (
    'RequestObject',
    'RequestConverter',
    'RequestFactory',
)


class RequestObject(t.Object):

    @property
    def content(self) -> ty.Any:
        return self.get('content', t.Undefined)

    @property
    def path_params(self) -> ty.Mapping[str, ty.Any]:
        return self['parameters'][o.PARAMETER_LOCATION.PATH]

    @property
    def query_params(self) -> ty.Mapping[str, ty.Any]:
        return self['parameters'][o.PARAMETER_LOCATION.QUERY]

    @property
    def header_params(self) -> ty.Mapping[str, ty.Any]:
        return self['parameters'][o.PARAMETER_LOCATION.HEADER]

    @property
    def cookie_params(self) -> ty.Mapping[str, ty.Any]:
        return self['parameters'][o.PARAMETER_LOCATION.COOKIE]


class RequestObjectType(t.ObjectType[RequestObject], result_class=RequestObject):

    __slots__ = ()


class RequestConverter:

    __slots__ = ('subtype', )

    def __init__(self, subtype: RequestObjectType):
        self.subtype = subtype

    def convert(
            self,
            path_params: ty.Mapping[str, ty.Any],
            query_params: ty.Mapping[str, ty.Any],
            headers: ty.Mapping[str, ty.Any],
            cookies: ty.Mapping[str, ty.Any],
            content: ty.Any = t.Undefined,
            content_type: ty.Optional[str] = None
    ) -> ty.Optional[RequestObject]:
        data = {
            'parameters': {
                o.PARAMETER_LOCATION.PATH: path_params,
                o.PARAMETER_LOCATION.QUERY: query_params,
                o.PARAMETER_LOCATION.HEADER: headers,
                o.PARAMETER_LOCATION.COOKIE: cookies
            }
        }

        if content is not t.Undefined and content_type is not None:
            data['content'] = {content_type: content}

        return self.subtype.convert(data, t.Path(), **make_request_conversion_context())


class RequestFactory:

    def __init__(self, type_factory: TypeFactory):
        self.type_factory = type_factory
        self.parameter_factory = ParameterFactory(self.type_factory)
        self.parameters_factory = ParametersFactory(self.parameter_factory)
        self.headers_factory = HeadersFactory(self.parameter_factory)
        self.media_type_factory = RequestMediaTypeFactory(self.type_factory, self.headers_factory)
        self.content_factory = ContentFactory(self.media_type_factory)
        self.request_body_factory = RequestBodyFactory(self.content_factory)

    def generate(
            self,
            parameters: ty.Optional[ty.Iterable[o.AnyParameterObject]] = None,
            request_body: ty.Optional[o.RequestBodyObject] = None
    ) -> RequestConverter:
        return RequestConverter(RequestObjectType(
            additional_properties=False,
            properties={
                'parameters': self.parameters_factory.generate(parameters),
                'content': t.AnyType() if request_body is None else self.request_body_factory.generate(request_body)
            }
        ))
