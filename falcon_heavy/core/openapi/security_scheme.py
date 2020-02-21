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
from .oauth_flows import OAuthFlowsObject, OAuthFlowsObjectType
from .constants import SECURITY_SCHEME_TYPE, PARAMETER_LOCATION

__all__ = (
    'BaseSecuritySchemeObject',
    'APIKeySecuritySchemeObject',
    'APIKeySecuritySchemeObjectType',
    'HttpSecuritySchemeObject',
    'HttpSecuritySchemeObjectType',
    'OAuth2SecuritySchemeObject',
    'OAuth2SecuritySchemeObjectType',
    'OpenIdConnectSecuritySchemeObject',
    'OpenIdConnectSecuritySchemeObjectType',
    'AnySecuritySchemeObject',
    'SecuritySchemePolymorphic',
)


class BaseSecuritySchemeObject(t.Object):

    @property
    def type(self) -> str:
        return self['type']

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')


T_base = ty.TypeVar('T_base', bound=BaseSecuritySchemeObject)


class BaseSecuritySchemeObjectType(BaseOpenAPIObjectType[T_base]):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'type': t.StringType(enum=SECURITY_SCHEME_TYPE),
        'description': t.StringType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'type'
    }


class APIKeySecuritySchemeObject(BaseSecuritySchemeObject):

    @property
    def name(self) -> str:
        return self['name']

    @property
    def location(self) -> str:
        return self['in']


class APIKeySecuritySchemeObjectType(
        BaseSecuritySchemeObjectType[APIKeySecuritySchemeObject], result_class=APIKeySecuritySchemeObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'name': t.StringType(),
        'in': t.StringType(
            enum=(PARAMETER_LOCATION.QUERY, PARAMETER_LOCATION.HEADER, PARAMETER_LOCATION.COOKIE)
        )
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'name',
        'in'
    }


class HttpSecuritySchemeObject(BaseSecuritySchemeObject):

    @property
    def scheme(self) -> str:
        return self['scheme']

    @property
    def bearer_format(self) -> ty.Optional[str]:
        return self.get('bearerFormat')


class HttpSecuritySchemeObjectType(
        BaseSecuritySchemeObjectType[HttpSecuritySchemeObject], result_class=HttpSecuritySchemeObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'scheme': t.StringType(),
        'bearerFormat': t.StringType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'scheme'
    }


class OAuth2SecuritySchemeObject(BaseSecuritySchemeObject):

    @property
    def flows(self) -> OAuthFlowsObject:
        return self['flows']


class OAuth2SecuritySchemeObjectType(
        BaseSecuritySchemeObjectType[OAuth2SecuritySchemeObject], result_class=OAuth2SecuritySchemeObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'flows': OAuthFlowsObjectType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'flows'
    }


class OpenIdConnectSecuritySchemeObject(BaseSecuritySchemeObject):

    @property
    def open_id_connect_url(self) -> str:
        return self['openIdConnectUrl']


class OpenIdConnectSecuritySchemeObjectType(
        BaseSecuritySchemeObjectType[OpenIdConnectSecuritySchemeObject],
        result_class=OpenIdConnectSecuritySchemeObject
):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'openIdConnectUrl': t.StringType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'openIdConnectUrl'
    }


AnySecuritySchemeObject = ty.Union[
    APIKeySecuritySchemeObject,
    HttpSecuritySchemeObject,
    OAuth2SecuritySchemeObject,
    OpenIdConnectSecuritySchemeObject
]


SecuritySchemePolymorphic = t.DiscriminatedType(
    property_name='type',
    mapping={
        'apiKey': APIKeySecuritySchemeObjectType(),
        'http': HttpSecuritySchemeObjectType(),
        'oauth2': OAuth2SecuritySchemeObjectType(),
        'openIdConnect': OpenIdConnectSecuritySchemeObjectType()
    }
)
