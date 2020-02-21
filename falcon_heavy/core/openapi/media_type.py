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
from falcon_heavy.core.utils import comma_delimited

from .base import BaseOpenAPIObjectType
from .schema import SchemaObject, SchemaObjectType
from .example import ExampleObject, ExampleObjectType
from .constants import SCHEMA_TYPE

__all__ = (
    'MediaTypeObject',
    'MediaTypeObjectType',
)


class MediaTypeObject(t.Object):

    @property
    def schema(self) -> ty.Optional[SchemaObject]:
        return self.get('schema')

    @property
    def example(self) -> ty.Optional[ty.Any]:
        return self.get('example')

    @property
    def examples(self) -> ty.Optional[ty.Mapping[str, ExampleObject]]:
        return self.get('examples')

    @property
    def encoding(self) -> ty.Optional[ty.Mapping[str, 'EncodingObject']]:
        return self.get('encoding')


class MediaTypeObjectType(BaseOpenAPIObjectType[MediaTypeObject], result_class=MediaTypeObject):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'missed_properties':
            "The key of `encoding`, being the property name, must exist in the `schema` as a property. "
            "The following properties must be defined in `properties` of `schema`: {}"
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'schema': t.ReferenceType[SchemaObject](SchemaObjectType()),
        'example': t.AnyType(),
        'examples': t.MapType[ExampleObject](t.ReferenceType[ExampleObject](ExampleObjectType())),
        'encoding': t.MapType['EncodingObject'](
            t.LazyType['EncodingObject'](lambda: EncodingObjectType()))
    }

    def validate_encoding(self, value: MediaTypeObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        encoding = value.encoding
        schema = value.schema

        if encoding is None or schema is None:
            return None

        if schema.type != SCHEMA_TYPE.OBJECT:
            return None

        if schema.properties_ is None:
            return None

        missed_properties: ty.List[str] = []
        for property_name, property_encoding in encoding.items():
            if property_name not in schema.properties_:
                missed_properties.append(property_name)

        if missed_properties:
            return self.messages['missed_properties'].format(
                comma_delimited(missed_properties))

        return None


from .encoding import EncodingObject, EncodingObjectType  # noqa
