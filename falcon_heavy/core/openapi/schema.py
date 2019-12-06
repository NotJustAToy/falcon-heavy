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
import warnings
import typing as ty
from collections import Mapping

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType
from .xml import XmlObject, XmlObjectType
from .external_documentation import ExternalDocumentationObject, ExternalDocumentationObjectType
from .discriminator import DiscriminatorObject, DiscriminatorObjectType
from .constants import SCHEMA_TYPE, SCHEMA_FORMAT, PRIMITIVE_SCHEMA_TYPES, PARAMETER_TYPE

__all__ = (
    'SchemaObject',
    'SchemaObjectType',
)


class SchemaObject(t.Object):

    def __init__(
            self,
            path: ty.Optional[t.Path] = None,
            ref: ty.Optional[str] = None,
            name: ty.Optional[str] = None,
            subschemas: ty.Optional[ty.List['SchemaObject']] = None,
            **kwargs: ty.Any
    ) -> None:
        super(SchemaObject, self).__init__(**kwargs)
        self.path = path
        self.ref = ref
        self.name = name
        self.subschemas = subschemas or []

    @property
    def type(self) -> ty.Optional[str]:
        return self.get('type')

    @property
    def format(self) -> ty.Optional[str]:
        return self.get('format')

    @property
    def title(self) -> ty.Optional[str]:
        return self.get('title')

    @property
    def description(self) -> ty.Optional[str]:
        return self.get('description')

    @property
    def default(self) -> ty.Optional[ty.Any]:
        return self.get('default', t.Undefined)

    @property
    def nullable(self) -> bool:
        return self['nullable']

    @property
    def enum(self) -> ty.Optional[ty.Sequence]:
        return self.get('enum')

    @property
    def read_only(self) -> bool:
        return self['readOnly']

    @property
    def write_only(self) -> bool:
        return self['writeOnly']

    @property
    def xml(self) -> ty.Optional[XmlObject]:
        return self.get('xml')

    @property
    def external_docs(self) -> ty.Optional[ExternalDocumentationObject]:
        return self.get('externalDocs')

    @property
    def example(self) -> ty.Optional[ty.Any]:
        return self.get('example')

    @property
    def deprecated(self) -> ty.Optional[bool]:
        return self['deprecated']

    @property
    def multiple_of(self) -> ty.Optional[t.Number]:
        return self.get('multipleOf')

    @property
    def minimum(self) -> ty.Optional[t.Number]:
        return self.get('minimum')

    @property
    def maximum(self) -> ty.Optional[t.Number]:
        return self.get('maximum')

    @property
    def exclusive_minimum(self) -> bool:
        return self['exclusiveMinimum']

    @property
    def exclusive_maximum(self) -> bool:
        return self['exclusiveMaximum']

    @property
    def min_length(self) -> int:
        return self['minLength']

    @property
    def max_length(self) -> ty.Optional[int]:
        return self.get('maxLength')

    @property
    def pattern(self) -> ty.Optional[ty.Pattern]:
        return self.get('pattern')

    @property
    def discriminator(self) -> ty.Optional[DiscriminatorObject]:
        return self.get('discriminator')

    @property
    def all_of(self) -> ty.Optional[ty.Sequence['SchemaObject']]:
        return self.get('allOf')

    @property
    def any_of(self) -> ty.Optional[ty.Sequence['SchemaObject']]:
        return self.get('anyOf')

    @property
    def one_of(self) -> ty.Optional[ty.Sequence['SchemaObject']]:
        return self.get('oneOf')

    @property
    def not_(self) -> ty.Optional[ty.Sequence['SchemaObject']]:
        return self.get('not')

    @property
    def items_(self) -> ty.Optional['SchemaObject']:
        return self.get('items')

    @property
    def min_items(self) -> int:
        return self['minItems']

    @property
    def max_items(self) -> ty.Optional[int]:
        return self.get('maxItems')

    @property
    def unique_items(self) -> bool:
        return self['uniqueItems']

    @property
    def required(self) -> ty.Optional[ty.Set[str]]:
        return self.get('required')

    @property
    def properties_(self) -> ty.Optional[ty.Mapping[str, 'SchemaObject']]:
        return self.get('properties')

    @property
    def min_properties(self) -> int:
        return self['minProperties']

    @property
    def max_properties(self) -> ty.Optional[int]:
        return self.get('maxProperties')

    @property
    def additional_properties_(self) -> ty.Union[bool, 'SchemaObject']:
        return self['additionalProperties']

    @property
    def pattern_properties_(self) -> ty.Optional[ty.Mapping[ty.Pattern, 'SchemaObject']]:
        return self.get('x-patternProperties')

    @property
    def default_content_type(self) -> ty.Optional[str]:
        if self.type in (SCHEMA_TYPE.ARRAY, SCHEMA_TYPE.OBJECT):
            return 'application/json'

        elif self.type == SCHEMA_TYPE.STRING and self.format in (SCHEMA_FORMAT.BINARY, SCHEMA_FORMAT.BYTE):
            return 'application/octet-stream'

        elif self.type is not None:
            return 'text/plain'

        else:
            return None

    @property
    def parameter_type(self) -> ty.Optional[str]:
        if self.type == SCHEMA_TYPE.ARRAY:
            return PARAMETER_TYPE.ARRAY

        elif self.type == SCHEMA_TYPE.OBJECT:
            return PARAMETER_TYPE.OBJECT

        elif self.type is not None:
            return PARAMETER_TYPE.PRIMITIVE

        return None

    def is_required(self, property_name):
        if self.required:
            return property_name in self.required

        return False


class ReferenceSaver(t.AbstractConvertible[SchemaObject]):

    __slots__ = ('subtype', )

    def __init__(self, subtype: t.ReferenceType[SchemaObject], **kwargs: ty.Any) -> None:
        self.subtype = subtype
        super(ReferenceSaver, self).__init__(**kwargs)

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[SchemaObject]:
        ref = None
        if isinstance(value, Mapping) and '$ref' in value:
            ref = value['$ref']

        result: ty.Optional[SchemaObject] = self.subtype.convert(value, path, **context)

        if result is None:
            return None

        result.ref = ref
        return result


T = ty.TypeVar('T', bound=SchemaObject)


class RegexMapType(t.AbstractConvertible[ty.Mapping[ty.Pattern, ty.Optional[T]]]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'invalid_key': "Key '{0}' is not a valid regular expression"
    }

    __slots__ = ('subtype', )

    def __init__(self, subtype: t.MapType[T], **kwargs):
        super(RegexMapType, self).__init__(**kwargs)
        self.subtype = subtype

    def convert(
            self,
            value: ty.Any,
            path: t.Path,
            *args: ty.Any,
            **context: ty.Any
    ) -> ty.Optional[ty.Mapping[ty.Pattern, ty.Optional[T]]]:
        mapping: ty.Optional[ty.Mapping[str, ty.Optional[T]]] = self.subtype.convert(value, path, *args, **context)

        if mapping is None:
            return None

        result: ty.Dict[ty.Pattern, ty.Optional[T]] = {}
        errors: ty.List[t.Error] = []
        for key in mapping.keys():
            try:
                result[re.compile(key)] = mapping[key]
            except re.error:
                errors.append(t.Error(path, self.messages['invalid_key'].format(key)))

        if errors:
            raise t.SchemaError(*errors)

        return result


TYPE_SPECIFIC_KEYWORDS: ty.Mapping[str, ty.Tuple[str, ...]] = {
    SCHEMA_TYPE.STRING: ('minLength', 'maxLength', 'pattern'),
    SCHEMA_TYPE.NUMBER: ('minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf'),
    SCHEMA_TYPE.OBJECT: ('properties', 'required', 'additionalProperties', 'minProperties', 'maxProperties'),
    SCHEMA_TYPE.ARRAY: ('items', 'minItems', 'maxItems', 'uniqueItems')
}


class SchemaObjectType(BaseOpenAPIObjectType[SchemaObject], result_class=SchemaObject):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'ambiguous_type': "The schema type is ambiguous",
        'deprecated': "The schema '{0}' is deprecated",
        'format': "Format is applicable only for primitive types",
        'items_required_for_type_array': "`items` must be specified for array type",
        'invalid_type_for_minimum': "`minimum` can only be used for number types",
        'invalid_type_for_maximum': "`maximum` can only be used for number types",
        'must_be_greater_than_minimum':
            "The value of `maximum` must be greater than or equal to the value of `minimum`",
        'exclusive_minimum_required_minimum': "When `exclusiveMinimum` is set, `minimum` is required",
        'exclusive_maximum_required_maximum': "When `exclusiveMaximum` is set, `maximum` is required",
        'invalid_type_for_multiple_of': "`multipleOf` can only be used for number types",
        'invalid_type_for_min_length': "`minLength` can only be used for string types",
        'invalid_type_for_max_length': "`maxLength` can only be used for string types",
        'must_be_greater_than_min_length':
            "The value of `maxLength` must be greater than or equal to the `minLength` value",
        'invalid_type_for_min_items': "`minItems` can only be used for array types",
        'invalid_type_for_max_items': "`maxItems` can only be used for array types",
        'must_be_greater_than_min_items':
            "The value of `maxItems` must be greater than or equal to the value of `minItems`",
        'invalid_type_for_unique_items': "`uniqueItems` can only be used for array types",
        'invalid_type_for_properties': "`properties` can only be used for object types",
        'invalid_type_for_additional_properties': "`additionalProperties` can only be used for object types",
        'invalid_type_for_required': "`required` can only be used for object types",
        'invalid_type_for_min_properties': "`minProperties` can only be used for object types",
        'invalid_type_for_max_properties': "`maxProperties` can only be used for object types",
        'must_be_greater_than_min_properties':
            "The value of `maxProperties` must be greater than or equal to `minProperties`",
        'improperly_discriminator_usage': "The `discriminator` can only be used with the keywords `anyOf` or `oneOf`",
        'read_only_and_write_only_are_mutually_exclusive':
            "`readOnly` and `writeOnly` are mutually exclusive and cannot be set simultaneously"
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'type': t.StringType(enum=SCHEMA_TYPE),
        'format': t.StringType(),
        'title': t.StringType(),
        'description': t.StringType(),
        'default': t.AnyType(),
        'nullable': t.BooleanType(default=False),
        'enum': t.ArrayType(t.AnyType(), min_items=1, unique_items=True),

        'readOnly': t.BooleanType(default=False),
        'writeOnly': t.BooleanType(default=False),
        'xml': XmlObjectType(),
        'externalDocs': ExternalDocumentationObjectType(),
        'example': t.AnyType(),
        'deprecated': t.BooleanType(default=False),

        'multipleOf': t.NumberType(minimum=0, exclusive_minimum=True),
        'minimum': t.NumberType(),
        'maximum': t.NumberType(),
        'exclusiveMinimum': t.BooleanType(default=False),
        'exclusiveMaximum': t.BooleanType(default=False),

        'minLength': t.IntegerType(minimum=0, default=0),
        'maxLength': t.IntegerType(minimum=0),
        'pattern': t.RegexType(t.StringType(min_length=1)),

        'discriminator': t.LazyType[DiscriminatorObject](lambda: DiscriminatorObjectType()),
        'allOf': t.ArrayType[SchemaObject](t.ReferenceType[SchemaObject](
            t.LazyType[SchemaObject](lambda: SchemaObjectType())), min_items=1),
        'anyOf': t.ArrayType[SchemaObject](ReferenceSaver(t.ReferenceType[SchemaObject](
            t.LazyType[SchemaObject](lambda: SchemaObjectType()))), min_items=1),
        'oneOf': t.ArrayType[SchemaObject](ReferenceSaver(t.ReferenceType[SchemaObject](
            t.LazyType[SchemaObject](lambda: SchemaObjectType()))), min_items=1),
        'not': t.ArrayType[SchemaObject](t.ReferenceType[SchemaObject](
            t.LazyType[SchemaObject](lambda: SchemaObjectType())), min_items=1),

        'items': t.ReferenceType[SchemaObject](t.LazyType[SchemaObject](lambda: SchemaObjectType())),
        'minItems': t.IntegerType(minimum=0, default=0),
        'maxItems': t.IntegerType(minimum=0),
        'uniqueItems': t.BooleanType(default=False),

        'required': t.ArrayType[str](t.StringType(), min_items=1, unique_items=True),
        'properties': t.MapType[SchemaObject](t.ReferenceType[SchemaObject](
            t.LazyType[SchemaObject](lambda: SchemaObjectType()))),
        'minProperties': t.IntegerType(minimum=0, default=0),
        'maxProperties': t.IntegerType(minimum=0),
        'additionalProperties': t.OneOfType([
            t.BooleanType(),
            t.ReferenceType[SchemaObject](t.LazyType[SchemaObject](lambda: SchemaObjectType()))
        ], default=True),
        'x-patternProperties': RegexMapType[SchemaObject](t.MapType[SchemaObject](
            t.LazyType[SchemaObject](lambda: SchemaObjectType())))
    }

    def _convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> SchemaObject:
        result: SchemaObject = super(SchemaObjectType, self)._convert(value, path, **context)

        if result.type is None:
            inferred = []
            for schema_type, keywords in TYPE_SPECIFIC_KEYWORDS.items():
                if any(keyword for keyword in keywords if keyword in value):
                    inferred.append(schema_type)

            if len(inferred) > 1:
                raise t.SchemaError(t.Error(path, self.messages['ambiguous_type']))

            elif inferred:
                result.properties['type'] = inferred[0]

        if result.deprecated:
            warnings.warn(self.messages['deprecated'].format(path), DeprecationWarning)

        if result.required:
            result.properties['required'] = set(result.required)

        result.path = path
        return result

    def validate_format(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.format is not None and value.type not in PRIMITIVE_SCHEMA_TYPES:
            return self.messages['format']

        return None

    def validate_items(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.type == SCHEMA_TYPE.ARRAY and value.items_ is None:
            return self.messages['items_required_for_type_array']

        return None

    def validate_discriminator(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.discriminator is None:
            return None

        if value.all_of is not None or value.not_ is not None:
            return self.messages['improperly_discriminator_usage']

        return None

    def validate_minimum(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.minimum is None:
            return None

        if value.type not in (SCHEMA_TYPE.NUMBER, SCHEMA_TYPE.INTEGER):
            return self.messages['invalid_type_for_minimum']

        return None

    def validate_maximum(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.maximum is None:
            return None

        if value.type not in (SCHEMA_TYPE.NUMBER, SCHEMA_TYPE.INTEGER):
            return self.messages['invalid_type_for_maximum']

        if value.minimum is not None and value.maximum < value.minimum:
            return self.messages['must_be_greater_than_minimum']

        return None

    def validate_exclusive_minimum(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'exclusiveMinimum' in original and value.minimum is None:
            return self.messages['exclusive_minimum_required_minimum']

        return None

    def validate_exclusive_maximum(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'exclusiveMaximum' in original and value.maximum is None:
            return self.messages['exclusive_maximum_required_maximum']

        return None

    def validate_multiple_of(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.multiple_of is not None and value.type not in (SCHEMA_TYPE.NUMBER, SCHEMA_TYPE.INTEGER):
            return self.messages['invalid_type_for_multiple_of']

        return None

    def validate_min_length(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'minLength' in original and value.type != SCHEMA_TYPE.STRING:
            return self.messages['invalid_type_for_min_length']

        return None

    def validate_max_length(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.max_length is None:
            return None

        if value.type != SCHEMA_TYPE.STRING:
            return self.messages['invalid_type_for_max_length']

        if value.max_length < value.min_length:
            return self.messages['must_be_greater_than_min_length']

        return None

    def validate_min_items(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'minItems' in original and value.type != SCHEMA_TYPE.ARRAY:
            return self.messages['invalid_type_for_min_items']

        return None

    def validate_max_items(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.max_items is None:
            return None

        if value.type != SCHEMA_TYPE.ARRAY:
            return self.messages['invalid_type_for_max_items']

        if value.max_items < value.min_items:
            return self.messages['must_be_greater_than_min_items']

        return None

    def validate_unique_items(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'uniqueItems' in original and value.type != SCHEMA_TYPE.ARRAY:
            return self.messages['invalid_type_for_unique_items']

        return None

    def validate_properties(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'properties' in original and value.type != SCHEMA_TYPE.OBJECT:
            return self.messages['invalid_type_for_properties']

        return None

    def validate_additional_properties(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'additionalProperties' in original and value.type != SCHEMA_TYPE.OBJECT:
            return self.messages['invalid_type_for_additional_properties']

        return None

    def validate_required(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'required' in original and value.type != SCHEMA_TYPE.OBJECT:
            return self.messages['invalid_type_for_required']

        return None

    def validate_min_properties(
            self,
            value: SchemaObject,
            original: ty.Mapping,
            *args: ty.Any,
            **context: ty.Any
    ) -> t.ValidationResult:
        if 'minProperties' in original and value.type != SCHEMA_TYPE.OBJECT:
            return self.messages['invalid_type_for_min_properties']

        return None

    def validate_max_properties(self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.max_properties is None:
            return None

        if value.type != SCHEMA_TYPE.OBJECT:
            return self.messages['invalid_type_for_max_properties']

        if value.max_properties < value.min_properties:
            return self.messages['must_be_greater_than_min_properties']

        return None

    def validate_read_only_write_only(
            self, value: SchemaObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if value.read_only and value.write_only:
            return self.messages['read_only_and_write_only_are_mutually_exclusive']

        return None
