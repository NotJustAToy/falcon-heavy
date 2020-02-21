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
from .server import ServerObject, ServerObjectType

__all__ = (
    'LinkObject',
    'LinkObjectType',
)


class LinkObject(t.Object):

    @property
    def operation_ref(self) -> ty.Optional[str]:
        return self.get('operationRef')

    @property
    def operation_id(self) -> ty.Optional[str]:
        return self.get('operationId')

    @property
    def parameters(self) -> ty.Optional[ty.Mapping[str, ty.Any]]:
        return self.get('parameters')

    @property
    def request_body(self) -> ty.Optional[ty.Any]:
        return self.get('requestBody')

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def server(self) -> ty.Optional[ServerObject]:
        return self.get('server')


class LinkObjectType(BaseOpenAPIObjectType[LinkObject], result_class=LinkObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'operationRef': t.StringType(),
        'operationId': t.StringType(),
        'parameters': t.MapType(t.AnyType()),
        'requestBody': t.AnyType(),
        'description': t.StringType(),
        'server': ServerObjectType()
    }
