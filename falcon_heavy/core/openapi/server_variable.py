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

__all__ = (
    'ServerVariableObject',
    'ServerVariableObjectType',
)


class ServerVariableObject(t.Object):

    @property
    def enum(self) -> ty.Optional[ty.Sequence[str]]:
        return self.get('enum')

    @property
    def default(self) -> str:
        return self['default']

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')


class ServerVariableObjectType(BaseOpenAPIObjectType[ServerVariableObject], result_class=ServerVariableObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'enum': t.ArrayType[str](t.StringType()),
        'default': t.StringType(),
        'description': t.StringType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'default'
    }
