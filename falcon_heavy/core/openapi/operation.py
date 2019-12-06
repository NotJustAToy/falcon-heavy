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

import warnings
import typing as ty

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType
from .external_documentation import ExternalDocumentationObject, ExternalDocumentationObjectType
from .parameter import AnyParameterObject, ParameterPolymorphic
from .responses import ResponsesObject, ResponsesObjectType
from .request_body import RequestBodyObject, RequestBodyObjectType
from .callback import CallbackObject, CallbackObjectType
from .server import ServerObject, ServerObjectType
from .security_requirement import SecurityRequirementObject, SecurityRequirementObjectType

__all__ = (
    'OperationIds',
    'OperationObject',
    'OperationObjectType',
)


OperationIds = ty.MutableMapping[str, t.Path]


class OperationObject(t.Object):

    @property
    def tags(self) -> ty.Optional[ty.Sequence[str]]:
        return self.get('tags')

    @property
    def summary(self) -> ty.Optional[str]:
        return self.get('summary')

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def external_docs(self) -> ty.Optional[ExternalDocumentationObject]:
        return self.get('externalDocs')

    @property
    def operation_id(self) -> ty.Optional[str]:
        return self.get('operationId')

    @property
    def parameters(self) -> ty.Optional[ty.Sequence[AnyParameterObject]]:
        return self.get('parameters')

    @property
    def request_body(self) -> ty.Optional[RequestBodyObject]:
        return self.get('requestBody')

    @property
    def responses(self) -> ResponsesObject:
        return self['responses']

    @property
    def callbacks(self) -> ty.Optional[ty.Mapping[str, CallbackObject]]:
        return self.get('callbacks')

    @property
    def deprecated(self) -> bool:
        return self['deprecated']

    @property
    def security(self) -> ty.Optional[ty.Sequence[SecurityRequirementObject]]:
        return self.get('security')

    @property
    def servers(self) -> ty.Optional[ty.Sequence[ServerObject]]:
        return self.get('servers')


class OperationObjectType(BaseOpenAPIObjectType[OperationObject], result_class=OperationObject):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'deprecated': "Operation '{0}' is deprecated",
        'operation_id': "Duplicate of operation ID '{0}' was found at '{1}'"
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'tags': t.ArrayType[str](t.StringType()),
        'summary': t.StringType(),
        'description': t.StringType(),
        'externalDocs': ExternalDocumentationObjectType(),
        'operationId': t.StringType(),
        'parameters': t.ArrayType[AnyParameterObject](
            t.ReferenceType[AnyParameterObject](ParameterPolymorphic),
            unique_items=True,
            unique_item_properties=['in', 'name']
        ),
        'requestBody': t.ReferenceType[RequestBodyObject](RequestBodyObjectType()),
        'responses': ResponsesObjectType(),
        'callbacks': t.MapType[CallbackObject](t.ReferenceType[CallbackObject](CallbackObjectType())),
        'deprecated': t.BooleanType(default=False),
        'security': t.ArrayType[SecurityRequirementObject](SecurityRequirementObjectType(min_properties=1)),
        'servers': t.ArrayType[ServerObject](ServerObjectType())
    }

    REQUIRED: ty.ClassVar[t.Required] = {
        'responses'
    }

    def convert(
            self,
            value: ty.Any,
            path: t.Path,
            *args: ty.Any,
            operation_ids: ty.Optional[OperationIds] = None,
            **context: ty.Any
    ) -> ty.Optional[OperationObject]:
        assert operation_ids is not None

        result: ty.Optional[OperationObject] = super(OperationObjectType, self).convert(value, path, **context)

        if result is None:
            return None

        if result.deprecated:
            warnings.warn(self.messages['deprecated'].format(path), DeprecationWarning)

        operation_id = result.operation_id
        if operation_id is not None:
            if operation_id in operation_ids:
                raise t.SchemaError(t.Error(
                    path / 'operationId',
                    self.messages['operation_id'].format(
                        operation_id, operation_ids[operation_id])
                ))

            operation_ids[operation_id] = path / 'operationId'

        return result
