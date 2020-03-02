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

import os
import typing as ty

from falcon_heavy.core import types as t, openapi as o

from .registry import registered, hashkey
from .utils import merge_schemas

__all__ = (
    'FormatFactory',
    'register_format_factory',
    'TypeFactory',
)

T = ty.TypeVar('T', bound=t.IntegerType)


def __generate_integer_type(schema: o.SchemaObject, type_class: ty.Type[T]) -> T:
    return type_class(
        nullable=schema.nullable,
        default=schema.default,
        minimum=schema.minimum,
        maximum=schema.maximum,
        exclusive_minimum=schema.exclusive_minimum,
        exclusive_maximum=schema.exclusive_maximum,
        multiple_of=schema.multiple_of,
        enum=schema.enum
    )


def _generate_integer_type(schema: o.SchemaObject) -> t.IntegerType:
    return __generate_integer_type(schema, type_class=t.IntegerType)


def _generate_int32_type(schema: o.SchemaObject) -> t.Int32Type:
    return __generate_integer_type(schema, type_class=t.Int32Type)


def _generate_int64_type(schema: o.SchemaObject) -> t.Int64Type:
    return __generate_integer_type(schema, type_class=t.Int64Type)


def _generate_number_type(schema: o.SchemaObject) -> t.NumberType:
    return t.NumberType(
        nullable=schema.nullable,
        default=schema.default,
        minimum=schema.minimum,
        maximum=schema.maximum,
        exclusive_minimum=schema.exclusive_minimum,
        exclusive_maximum=schema.exclusive_maximum,
        multiple_of=schema.multiple_of,
        enum=schema.enum
    )


def _generate_string_type(schema: o.SchemaObject) -> t.StringType:
    return t.StringType(
        nullable=schema.nullable,
        default=schema.default,
        min_length=schema.min_length,
        max_length=schema.max_length,
        enum=schema.enum,
        pattern=schema.pattern
    )


def _generate_boolean_type(schema: o.SchemaObject) -> t.BooleanType:
    return t.BooleanType(
        nullable=schema.nullable,
        default=schema.default,
        enum=schema.enum
    )


def _generate_date_type(schema: o.SchemaObject) -> t.DateType:
    return t.DateType(_generate_string_type(schema))


def _generate_datetime_type(schema: o.SchemaObject) -> t.DateTimeType:
    return t.DateTimeType(_generate_string_type(schema))


def _generate_byte_type(schema: o.SchemaObject) -> t.ByteType:
    return t.ByteType(_generate_string_type(schema))


def _generate_binary_type(schema: o.SchemaObject) -> t.BinaryType:
    return t.BinaryType(
        nullable=schema.nullable
    )


def _generate_any_type(schema: o.SchemaObject) -> t.AnyType:
    return t.AnyType(
        nullable=schema.nullable,
        default=schema.default,
        enum=schema.enum
    )


FormatFactory = ty.Callable[[o.SchemaObject], t.AbstractConvertible]


_format_factories: ty.Dict[ty.Tuple[str, str], FormatFactory] = {
    (o.SCHEMA_TYPE.INTEGER, o.SCHEMA_FORMAT.INT32): _generate_int32_type,
    (o.SCHEMA_TYPE.INTEGER, o.SCHEMA_FORMAT.INT64): _generate_int64_type,
    (o.SCHEMA_TYPE.NUMBER, o.SCHEMA_FORMAT.FLOAT): _generate_number_type,
    (o.SCHEMA_TYPE.NUMBER, o.SCHEMA_FORMAT.DOUBLE): _generate_number_type,
    (o.SCHEMA_TYPE.STRING, o.SCHEMA_FORMAT.BYTE): _generate_byte_type,
    (o.SCHEMA_TYPE.STRING, o.SCHEMA_FORMAT.BINARY): _generate_binary_type,
    (o.SCHEMA_TYPE.STRING, o.SCHEMA_FORMAT.DATE): _generate_date_type,
    (o.SCHEMA_TYPE.STRING, o.SCHEMA_FORMAT.DATETIME): _generate_datetime_type,
    (o.SCHEMA_TYPE.STRING, o.SCHEMA_FORMAT.PASSWORD): _generate_string_type
}


def register_format_factory(type_: str, format_: str, factory: FormatFactory) -> None:
    _format_factories[(type_, format_)] = factory


class TypeFactory:

    def _generate_array_type(self, schema: o.SchemaObject) -> t.ArrayType:
        return t.ArrayType(
            item_type=self.generate(schema.items_),
            nullable=schema.nullable,
            default=schema.default,
            unique_items=schema.unique_items,
            min_items=schema.min_items,
            max_items=schema.max_items,
            enum=schema.enum
        )

    def _generate_object_type(self, schema: o.SchemaObject) -> t.ObjectType:
        properties = {}
        read_only = set()
        write_only = set()
        if schema.properties_:
            for property_name, property_schema in schema.properties_.items():
                if property_schema.read_only:
                    read_only.add(property_name)

                if property_schema.write_only:
                    write_only.add(property_name)

                properties[property_name] = self.generate(property_schema)

        if isinstance(schema.additional_properties_, bool):
            additional_properties = schema.additional_properties_
        else:
            additional_properties = self.generate(schema.additional_properties_)

        pattern_properties = {}
        if schema.x_pattern_properties:
            for pattern, property_schema in schema.x_pattern_properties.items():
                pattern_properties[pattern] = self.generate(property_schema)

        return t.ObjectType(
            properties=properties,
            required=schema.required,
            additional_properties=additional_properties,
            pattern_properties=pattern_properties,
            read_only=read_only,
            write_only=write_only,
            nullable=schema.nullable,
            default=schema.default,
            enum=schema.enum,
            min_properties=schema.min_properties,
            max_properties=schema.max_properties,
            messages={
                'additional_properties': (
                    "When `additionalProperties` is False, no unspecified properties are "
                    "allowed. The following unspecified properties were found: {0}"
                )
            }
        )

    def _generate_polymorphic_type(
            self,
            discriminator: o.DiscriminatorObject,
            subschemas: ty.Iterable[o.SchemaObject]
    ) -> t.DiscriminatedType:
        subschema_types: ty.Dict[str, t.AbstractConvertible] = {
            subschema.name: self.generate(subschema)
            for subschema in subschemas
            if subschema.name is not None
        }

        mapping: ty.Dict[str, t.AbstractConvertible] = {}
        for name, subschema_type in subschema_types.items():
            mapping[name] = subschema_type

        if discriminator.mapping:
            for value, name in discriminator.mapping.items():
                if name in subschema_types:
                    mapping[value] = subschema_types[name]

        return t.DiscriminatedType(
            property_name=discriminator.property_name,
            mapping=mapping
        )

    def _generate_discriminated_type(
            self,
            discriminator: o.DiscriminatorObject,
            subschemas: ty.Iterable[o.SchemaObject],
            nullable: bool
    ) -> t.DiscriminatedType:
        subschema_types: ty.Dict[str, t.AbstractConvertible] = {
            subschema.ref: self.generate(subschema)
            for subschema in subschemas
            if subschema.ref is not None
        }

        mapping: ty.Dict[str, t.AbstractConvertible] = {}
        for ref, subschema_type in subschema_types.items():
            mapping[os.path.splitext(os.path.basename(ref))[0]] = subschema_type

        if discriminator.mapping:
            for value, ref in discriminator.mapping.items():
                if ref in subschema_types:
                    mapping[value] = subschema_types[ref]

        return t.DiscriminatedType(
            property_name=discriminator.property_name,
            mapping=mapping,
            nullable=nullable
        )

    def _generate_merged(self, schema: o.SchemaObject) -> t.AbstractConvertible:
        assert schema.all_of is not None
        return self._generate_no_register(merge_schemas(schema.all_of))

    def _generate_allof_type(self, schema: o.SchemaObject) -> t.AllOfType:
        assert schema.all_of is not None
        return t.AllOfType(
            subtypes=[self.generate(subschema, allow_model_level_polymorphic=bool(i))
                      for i, subschema in enumerate(schema.all_of)],
            nullable=schema.nullable,
            default=schema.default,
            enum=schema.enum
        )

    def _generate_anyof_type(self, schema: o.SchemaObject) -> t.AnyOfType:
        assert schema.any_of is not None
        return t.AnyOfType(
            subtypes=[self.generate(subschema) for subschema in schema.any_of],
            nullable=schema.nullable,
            default=schema.default,
            enum=schema.enum
        )

    def _generate_oneof_type(self, schema: o.SchemaObject) -> t.OneOfType:
        assert schema.one_of is not None
        return t.OneOfType(
            subtypes=[self.generate(subschema) for subschema in schema.one_of],
            nullable=schema.nullable,
            default=schema.default,
            enum=schema.enum
        )

    def _generate_not_type(self, schema: o.SchemaObject) -> t.NotType:
        assert schema.not_ is not None
        return t.NotType(
            subtypes=[self.generate(subschema) for subschema in schema.not_],
            nullable=schema.nullable
        )

    def _generate_no_register(
            self, schema: o.SchemaObject, allow_model_level_polymorphic: bool = True) -> t.AbstractConvertible:
        format_factory: ty.Optional[FormatFactory] = None
        if schema.type is not None and schema.format is not None:
            format_factory = _format_factories.get((schema.type, schema.format))

        if format_factory is not None:
            return format_factory(schema)

        elif schema.type == o.SCHEMA_TYPE.STRING:
            return _generate_string_type(schema)

        elif schema.type == o.SCHEMA_TYPE.NUMBER:
            return _generate_number_type(schema)

        elif schema.type == o.SCHEMA_TYPE.INTEGER:
            return _generate_integer_type(schema)

        elif schema.type == o.SCHEMA_TYPE.BOOLEAN:
            return _generate_boolean_type(schema)

        elif schema.type == o.SCHEMA_TYPE.ARRAY:
            return self._generate_array_type(schema)

        elif (
                schema.type == o.SCHEMA_TYPE.OBJECT and
                schema.discriminator and
                schema.subschemas and
                allow_model_level_polymorphic
        ):
            return self._generate_polymorphic_type(schema.discriminator, schema.subschemas)

        elif schema.type == o.SCHEMA_TYPE.OBJECT:
            return self._generate_object_type(schema)

        elif schema.discriminator and schema.any_of:
            return self._generate_discriminated_type(schema.discriminator, schema.any_of, schema.nullable)

        elif schema.discriminator and schema.one_of:
            return self._generate_discriminated_type(schema.discriminator, schema.one_of, schema.nullable)

        elif schema.is_mergeable:
            return self._generate_merged(schema)

        elif schema.all_of:
            return self._generate_allof_type(schema)

        elif schema.any_of:
            return self._generate_anyof_type(schema)

        elif schema.one_of:
            return self._generate_oneof_type(schema)

        elif schema.not_:
            return self._generate_not_type(schema)

        else:
            return _generate_any_type(schema)

    @registered(key=lambda schema, allow_model_level_polymorphic=True: hashkey(
        schema.path, allow_model_level_polymorphic=allow_model_level_polymorphic))
    def generate(
            self, schema: o.SchemaObject, allow_model_level_polymorphic: bool = True) -> t.AbstractConvertible:
        return self._generate_no_register(schema, allow_model_level_polymorphic=allow_model_level_polymorphic)
