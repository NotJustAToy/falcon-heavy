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
from .contact import ContactObject, ContactObjectType
from .license import LicenseObject, LicenseObjectType

__all__ = (
    'InfoObject',
    'InfoObjectType',
)


class InfoObject(t.Object):

    @property
    def title(self) -> str:
        return self['title']

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def terms_of_service(self) -> ty.Optional[str]:
        return self.get('termsOfService')

    @property
    def contact(self) -> ty.Optional[ContactObject]:
        return self.get('contact')

    @property
    def license(self) -> ty.Optional[LicenseObject]:
        return self.get('license')

    @property
    def version(self) -> str:
        return self['version']


class InfoObjectType(BaseOpenAPIObjectType[InfoObject], result_class=InfoObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'title': t.StringType(),
        'description': t.StringType(),
        'termsOfService': t.URIType(),
        'contact': ContactObjectType(),
        'license': LicenseObjectType(),
        'version': t.StringType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'title',
        'version'
    }
