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
    'ContactObject',
    'ContactObjectType',
)


class ContactObject(t.Object):

    @property
    def name(self) -> ty.Optional[str]:
        return self.get('name')

    @property
    def url(self) -> ty.Optional[str]:
        return self.get('url')

    @property
    def email(self) -> ty.Optional[str]:
        return self.get('email')


class ContactObjectType(BaseOpenAPIObjectType[ContactObject], result_class=ContactObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'name': t.StringType(),
        'url': t.URIType(),
        'email': t.EmailType()
    }
