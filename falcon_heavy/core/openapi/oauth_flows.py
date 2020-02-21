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
from .oauth_flow import OAuthFlowObject, OAuthFlowObjectType

__all__ = (
    'OAuthFlowsObject',
    'OAuthFlowsObjectType',
)


class OAuthFlowsObject(t.Object):

    @property
    def implicit(self) -> ty.Optional[OAuthFlowObject]:
        return self.get('implicit')

    @property
    def password(self) -> ty.Optional[OAuthFlowObject]:
        return self.get('password')

    @property
    def client_credentials(self) -> ty.Optional[OAuthFlowObject]:
        return self.get('clientCredentials')

    @property
    def authorization_code(self) -> ty.Optional[OAuthFlowObject]:
        return self.get('authorizationCode')


class OAuthFlowsObjectType(BaseOpenAPIObjectType[OAuthFlowsObject], result_class=OAuthFlowsObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'implicit': OAuthFlowObjectType(),
        'password': OAuthFlowObjectType(),
        'clientCredentials': OAuthFlowObjectType(),
        'authorizationCode': OAuthFlowObjectType()
    }
