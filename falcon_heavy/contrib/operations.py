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

import operator
import typing as ty
from collections import ChainMap

from cachetools import cachedmethod, LRUCache

from falcon_heavy.core import types as t, openapi as o, factories as f

from .path import OpenAPIPath

__all__ = (
    'OperationFindingError',
    'OperationNotFoundError',
    'OperationMultipleFoundError',
    'OpenAPIOperation',
    'OpenAPIOperations',
)


class OperationFindingError(Exception):
    pass


class OperationNotFoundError(OperationFindingError):
    pass


class OperationMultipleFoundError(OperationFindingError):
    pass


class OpenAPIOperation(ty.NamedTuple):
    operation_id: ty.Optional[str]
    method: str
    servers: ty.Optional[ty.Iterable[o.ServerObject]]
    request_converter: f.RequestConverter
    response_converter: f.ResponseConverter
    security: ty.Iterable[ty.Mapping[str, ty.Iterable[str]]]
    security_schemes: ty.Mapping[str, o.AnySecuritySchemeObject]
    summary: ty.Optional[str]
    description: ty.Optional[str]
    extensions: ty.Mapping[str, ty.Any]


T = ty.TypeVar('T', bound='OpenAPIOperations')


class OpenAPIOperations(ty.Dict[OpenAPIPath, ty.Dict[str, OpenAPIOperation]]):

    def __init__(self, *args: ty.Any, **kwargs: ty.Any) -> None:
        super(OpenAPIOperations, self).__init__(*args, **kwargs)
        self._cache = LRUCache(1024)

    @classmethod
    def from_file(cls: ty.Type[T], path: str, handlers: ty.Optional[t.RefHandlers] = None) -> T:
        openapi_object: o.OpenAPIObject = o.load_specification(
            path, handlers=handlers)
        return cls.from_openapi_object(openapi_object)

    @classmethod
    def from_openapi_object(cls: ty.Type[T], openapi_object: o.OpenAPIObject) -> T:
        self = cls()

        type_factory = f.TypeFactory()
        request_factory = f.RequestFactory(type_factory)
        responses_factory = f.ResponsesFactory(type_factory)

        security_schemes: ty.Mapping[str, o.AnySecuritySchemeObject] = (
            {} if openapi_object.components is None else openapi_object.components.security_schemes or {})

        global_servers = openapi_object.servers
        global_security = openapi_object.security or []

        for template, path_item in openapi_object.paths.items():

            path_level_servers = path_item.servers or global_servers

            mapping: ty.Dict[str, OpenAPIOperation] = self.setdefault(
                OpenAPIPath(template), {})

            for method in o.HTTP_METHODS:
                operation: ty.Optional[o.OperationObject] = path_item.get(method)

                if operation is None:
                    continue

                operation_level_servers = operation.servers or path_level_servers
                operation_level_security = global_security
                if operation.security is not None:
                    operation_level_security = operation.security

                mapping[method] = OpenAPIOperation(
                    operation_id=operation.operation_id,
                    method=method,
                    servers=operation_level_servers,
                    request_converter=request_factory.generate(
                        parameters=operation.parameters,
                        request_body=operation.request_body
                    ),
                    response_converter=responses_factory.generate(
                        operation.responses
                    ),
                    security=operation_level_security,
                    security_schemes=security_schemes,
                    summary=operation.summary,
                    description=operation.description,
                    extensions=ChainMap(
                        operation.pattern_properties,
                        path_item.pattern_properties,
                        openapi_object.pattern_properties
                    )
                )

        return self

    @cachedmethod(operator.attrgetter('_cache'))
    def find(self, path: str, method: str, return_first: bool = True) -> OpenAPIOperation:
        method = method.lower()
        found = []
        for uri_template, mapping in self.items():
            if uri_template.match(path) and method in mapping:
                if return_first:
                    return mapping[method]
                found.append(mapping[method])

        if not found:
            raise OperationNotFoundError()

        if len(found) > 1:
            raise OperationMultipleFoundError()

        return found[0]
