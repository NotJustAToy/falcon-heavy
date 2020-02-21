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

__all__ = (
    'DiscriminatorObject',
    'DiscriminatorObjectType',
)


class DiscriminatorObject(t.Object):

    @property
    def property_name(self) -> str:
        return self['propertyName']

    @property
    def mapping(self) -> ty.Optional[ty.Mapping[str, str]]:
        return self.get('mapping')


class DiscriminatorObjectType(BaseOpenAPIObjectType[DiscriminatorObject], result_class=DiscriminatorObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'propertyName': t.StringType(min_length=1),
        'mapping': t.MapType[str](t.StringType(min_length=1))
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'propertyName'
    }
