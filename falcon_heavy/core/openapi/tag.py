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
from .external_documentation import ExternalDocumentationObject, ExternalDocumentationObjectType

__all__ = (
    'TagObject',
    'TagObjectType',
)


class TagObject(t.Object):

    @property
    def name(self) -> str:
        return self['name']

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def external_docs(self) -> ty.Optional[ExternalDocumentationObject]:
        return self.get('externalDocs')


class TagObjectType(BaseOpenAPIObjectType[TagObject], result_class=TagObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'name': t.StringType(),
        'description': t.StringType(),
        'externalDocs': ExternalDocumentationObjectType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'name'
    }
