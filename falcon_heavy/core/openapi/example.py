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
    'ExampleObject',
    'ExampleObjectType',
)


class ExampleObject(t.Object):

    @property
    def summary(self) -> ty.Optional[str]:
        return self.get('summary')

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def value(self) -> ty.Optional[ty.Any]:
        return self.get('value')

    @property
    def external_value(self) -> ty.Optional[str]:
        return self.get('externalValue')


class ExampleObjectType(BaseOpenAPIObjectType[ExampleObject], result_class=ExampleObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'summary': t.StringType(),
        'description': t.StringType(),
        'value': t.AnyType(),
        'externalValue': t.StringType()
    }
