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

import re
import typing as ty

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType
from .external_documentation import ExternalDocumentationObject, ExternalDocumentationObjectType
from .paths import PathsObject, PathsObjectType
from .operation import OperationObject
from .info import InfoObject, InfoObjectType
from .security_scheme import AnySecuritySchemeObject
from .security_requirement import SecurityRequirementObject, SecurityRequirementObjectType
from .tag import TagObject, TagObjectType
from .server import ServerObject, ServerObjectType
from .components import ComponentsObject, ComponentsObjectType
from .constants import HTTP_METHODS

__all__ = (
    'OpenAPIObject',
    'OpenAPIObjectType',
)


class OpenAPIObject(t.Object):

    @property
    def openapi(self) -> str:
        return self['openapi']

    @property
    def info(self) -> InfoObject:
        return self['info']

    @property
    def servers(self) -> ty.Optional[ty.Sequence[ServerObject]]:
        return self.get('servers')

    @property
    def paths(self) -> PathsObject:
        return self['paths']

    @property
    def components(self) -> ty.Optional[ComponentsObject]:
        return self.get('components')

    @property
    def security(self) -> ty.Optional[ty.Sequence[SecurityRequirementObject]]:
        return self.get('security')

    @property
    def tags(self) -> ty.Optional[ty.Sequence[TagObject]]:
        return self.get('tags')

    @property
    def external_docs(self) -> ty.Optional[ExternalDocumentationObject]:
        return self.get('externalDocs')


class OpenAPIObjectType(BaseOpenAPIObjectType[OpenAPIObject], result_class=OpenAPIObject):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'undefined_security_scheme': "Undefined security scheme '{0}'"
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'openapi': t.StringType(
            pattern=re.compile(r'^3\.0\.[0-2]$'),
            messages={'pattern': "Unsupported version of OpenAPI"}
        ),
        'info': InfoObjectType(),
        'servers': t.ArrayType[ServerObject](ServerObjectType()),
        'paths': PathsObjectType(),
        'components': ComponentsObjectType(),
        'security': t.ArrayType[SecurityRequirementObject](SecurityRequirementObjectType(min_properties=1)),
        'tags': t.ArrayType[TagObject](TagObjectType(), unique_items=True, unique_item_properties=['name']),
        'externalDocs': ExternalDocumentationObjectType()
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'openapi',
        'info',
        'paths'
    }

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[OpenAPIObject]:
        result: ty.Optional[OpenAPIObject] = super(OpenAPIObjectType, self).convert(value, path, **context)

        if result is None:
            return None

        security_schemes: ty.Mapping[str, AnySecuritySchemeObject] = {}
        components: ty.Optional[ComponentsObject] = result.components
        if components is not None and components.security_schemes:
            security_schemes = components.security_schemes

        errors: ty.List[t.Error] = []
        security: ty.Optional[ty.Sequence[SecurityRequirementObject]] = result.security
        if security:
            for i, security_requirement in enumerate(security):
                for scheme_name in security_requirement.additional_properties.keys():
                    if scheme_name not in security_schemes:
                        errors.append(t.Error(
                            path / 'security' / i,
                            self.messages['undefined_security_scheme'].format(scheme_name)
                        ))

        paths: PathsObject = result.paths
        for path_, path_item in paths.pattern_properties.items():
            for http_method in HTTP_METHODS:
                if http_method not in path_item:
                    continue

                operation: OperationObject = path_item[http_method]
                security = operation.security
                if security is None:
                    continue
                for i, security_requirement in enumerate(security):
                    for scheme_name in security_requirement.additional_properties.keys():
                        if scheme_name not in security_schemes:
                            errors.append(t.Error(
                                path / 'paths' / path_ / http_method / 'security' / i,
                                self.messages['undefined_security_scheme'].format(scheme_name)
                            ))

        if errors:
            raise t.SchemaError(*errors)

        return result
