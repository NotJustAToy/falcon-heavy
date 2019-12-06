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
from collections import ChainMap

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType
from .operation import OperationObject, OperationObjectType
from .server import ServerObject, ServerObjectType
from .parameter import AnyParameterObject, ParameterPolymorphic
from .constants import HTTP_METHODS

__all__ = (
    'PathItemObject',
    'PathItemObjectType',
)


class PathItemObject(t.Object):

    @property
    def summary(self) -> ty.Optional[str]:
        return self.get('summary')

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def get_(self) -> ty.Optional[OperationObject]:
        return self.get('get')

    @property
    def put(self) -> ty.Optional[OperationObject]:
        return self.get('put')

    @property
    def post(self) -> ty.Optional[OperationObject]:
        return self.get('post')

    @property
    def delete(self) -> ty.Optional[OperationObject]:
        return self.get('delete')

    @property
    def options(self) -> ty.Optional[OperationObject]:
        return self.get('options')

    @property
    def head(self) -> ty.Optional[OperationObject]:
        return self.get('head')

    @property
    def patch(self) -> ty.Optional[OperationObject]:
        return self.get('patch')

    @property
    def trace(self) -> ty.Optional[OperationObject]:
        return self.get('trace')

    @property
    def servers(self) -> ty.Optional[ty.Sequence[ServerObject]]:
        return self.get('servers')

    @property
    def parameters(self) -> ty.Optional[ty.Sequence[AnyParameterObject]]:
        return self.get('parameters')


class PathItemObjectType(BaseOpenAPIObjectType[PathItemObject], result_class=PathItemObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'summary': t.StringType(),
        'description': t.StringType(),

        'get': OperationObjectType(),
        'put': OperationObjectType(),
        'post': OperationObjectType(),
        'delete': OperationObjectType(),
        'options': OperationObjectType(),
        'head': OperationObjectType(),
        'patch': OperationObjectType(),
        'trace': OperationObjectType(),

        'servers': t.ArrayType[ServerObject](ServerObjectType()),
        'parameters': t.ArrayType[AnyParameterObject](
            t.ReferenceType[AnyParameterObject](ParameterPolymorphic),
            unique_items=True,
            unique_item_properties=('in', 'name')
        )
    }

    @staticmethod
    def _parameters_dict(
            parameters: ty.Sequence[AnyParameterObject]) -> ty.Mapping[ty.Tuple[str, str], AnyParameterObject]:
        return {(parameter['in'], parameter['name']): parameter for parameter in parameters}

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[PathItemObject]:
        result: ty.Optional[PathItemObject] = super(PathItemObjectType, self).convert(value, path, **context)

        if result is None:
            return None

        # Update parameters of each operation by common parameters
        common_parameters = result.parameters
        if common_parameters is not None:
            parameters_dict = self._parameters_dict(common_parameters)

            for http_method in HTTP_METHODS:
                operation: ty.Optional[OperationObject] = result.get(http_method)

                if operation is None:
                    continue

                parameters = operation.parameters
                if parameters is None:
                    operation.properties['parameters'] = parameters_dict.values()

                else:
                    operation.properties['parameters'] = ChainMap(
                        self._parameters_dict(parameters), parameters_dict).values()

        return result
