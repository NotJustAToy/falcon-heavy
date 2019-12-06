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
from falcon_heavy.core.utils import comma_delimited

from .base import BaseOpenAPIObjectType
from .schema import SchemaObject, SchemaObjectType
from .request_body import RequestBodyObject, RequestBodyObjectType
from .response import ResponseObject, ResponseObjectType
from .parameter import AnyParameterObject, ParameterPolymorphic
from .example import ExampleObject, ExampleObjectType
from .header import HeaderObject, HeaderObjectType
from .security_scheme import AnySecuritySchemeObject, SecuritySchemePolymorphic
from .link import LinkObject, LinkObjectType
from .callback import CallbackObject, CallbackObjectType
from .constants import SCHEMA_TYPE

__all__ = (
    'ComponentsObject',
    'ComponentsObjectType',
)

COMPONENT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\.\-_]+$')


class ComponentNameValidator(t.AbstractValidator[ty.Mapping[str, ty.Any]]):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'invalid_names': "The following component names are invalid: {0}"
    }

    def __call__(self, value: ty.Mapping[str, ty.Any], *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        invalid_names = []
        for name in value.keys():
            if not COMPONENT_NAME_PATTERN.match(name):
                invalid_names.append(name)

        if invalid_names:
            return self.messages['invalid_names'].format(comma_delimited(invalid_names))

        return None


COMPONENT_NAME_VALIDATOR = ComponentNameValidator()


class ComponentsObject(t.Object):

    @property
    def schemas(self) -> ty.Optional[ty.Mapping[str, SchemaObject]]:
        return self.get('schemas')

    @property
    def responses(self) -> ty.Optional[ty.Mapping[str, ResponseObject]]:
        return self.get('responses')

    @property
    def parameters(self) -> ty.Optional[ty.Mapping[str, AnyParameterObject]]:
        return self.get('parameters')

    @property
    def examples(self) -> ty.Optional[ty.Mapping[str, ExampleObject]]:
        return self.get('examples')

    @property
    def request_bodies(self) -> ty.Optional[ty.Mapping[str, RequestBodyObject]]:
        return self.get('requestBodies')

    @property
    def headers(self) -> ty.Optional[ty.Mapping[str, HeaderObject]]:
        return self.get('headers')

    @property
    def security_schemes(self) -> ty.Optional[ty.Mapping[str, AnySecuritySchemeObject]]:
        return self.get('securitySchemes')

    @property
    def links(self) -> ty.Optional[ty.Mapping[str, LinkObject]]:
        return self.get('links')

    @property
    def callbacks(self) -> ty.Optional[ty.Mapping[str, CallbackObject]]:
        return self.get('callbacks')


class ComponentsObjectType(BaseOpenAPIObjectType[ComponentsObject], result_class=ComponentsObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'schemas': t.MapType[SchemaObject](
            t.ReferenceType[SchemaObject](SchemaObjectType()), validators=(COMPONENT_NAME_VALIDATOR,)),
        'responses': t.MapType[ResponseObject](
            t.ReferenceType[ResponseObject](ResponseObjectType()), validators=(COMPONENT_NAME_VALIDATOR,)),
        'parameters': t.MapType[AnyParameterObject](
            t.ReferenceType[AnyParameterObject](ParameterPolymorphic), validators=(COMPONENT_NAME_VALIDATOR,)),
        'examples': t.MapType[ExampleObject](
            t.ReferenceType[ExampleObject](ExampleObjectType()), validators=(COMPONENT_NAME_VALIDATOR,)),
        'requestBodies': t.MapType[RequestBodyObject](
            t.ReferenceType[RequestBodyObject](RequestBodyObjectType()), validators=(COMPONENT_NAME_VALIDATOR,)),
        'headers': t.MapType[HeaderObject](
            t.ReferenceType[HeaderObject](HeaderObjectType()), validators=(COMPONENT_NAME_VALIDATOR,)),
        'securitySchemes': t.MapType[AnySecuritySchemeObject](t.ReferenceType[AnySecuritySchemeObject](
            SecuritySchemePolymorphic), validators=(COMPONENT_NAME_VALIDATOR,)),
        'links': t.MapType[LinkObject](
            t.ReferenceType[LinkObject](LinkObjectType()), validators=(COMPONENT_NAME_VALIDATOR,)),
        'callbacks': t.MapType[CallbackObject](
            t.ReferenceType[CallbackObject](CallbackObjectType()), validators=(COMPONENT_NAME_VALIDATOR,))
    }

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[ComponentsObject]:
        result: ty.Optional[ComponentsObject] = super(ComponentsObjectType, self).convert(value, path, **context)

        if result is None:
            return None

        schemas = result.schemas

        if not schemas:
            return result

        for name, schema in schemas.items():
            schema.name = name

            all_of = schema.all_of

            if all_of is None or schema.type is not None:
                continue

            top_subschema = all_of[0]
            if top_subschema.type == SCHEMA_TYPE.OBJECT and top_subschema.discriminator is not None:
                top_subschema.subschemas.append(schema)

        return result
