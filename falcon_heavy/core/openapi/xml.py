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
    'XmlObject',
    'XmlObjectType',
)


class XmlObject(t.Object):

    @property
    def name(self) -> ty.Optional[str]:
        return self.get('name')

    @property
    def namespace(self) -> ty.Optional[str]:
        return self.get('namespace')

    @property
    def prefix(self) -> ty.Optional[str]:
        return self.get('prefix')

    @property
    def attribute(self) -> bool:
        return self['attribute']

    @property
    def wrapped(self) -> bool:
        return self['wrapped']


class XmlObjectType(BaseOpenAPIObjectType[XmlObject], result_class=XmlObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'name': t.StringType(),
        'namespace': t.StringType(),
        'prefix': t.StringType(),
        'attribute': t.BooleanType(default=False),
        'wrapped': t.BooleanType(default=False)
    }
