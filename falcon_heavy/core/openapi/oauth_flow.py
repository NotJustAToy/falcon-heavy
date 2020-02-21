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
    'OAuthFlowObject',
    'OAuthFlowObjectType',
)


class OAuthFlowObject(t.Object):

    @property
    def authorization_url(self) -> str:
        return self['authorizationUrl']

    @property
    def token_url(self) -> str:
        return self['tokenUrl']

    @property
    def refresh_url(self) -> ty.Optional[str]:
        return self.get('refreshUrl')

    @property
    def scopes(self) -> ty.Mapping[str, str]:
        return self['scopes']


class OAuthFlowObjectType(BaseOpenAPIObjectType[OAuthFlowObject], result_class=OAuthFlowObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'authorizationUrl': t.StringType(),
        'tokenUrl': t.StringType(),
        'refreshUrl': t.StringType(),
        'scopes': t.MapType[str](t.StringType())
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'authorizationUrl',
        'tokenUrl',
        'scopes'
    }
