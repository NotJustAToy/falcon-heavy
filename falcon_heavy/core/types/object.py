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
from collections import Mapping, ChainMap

import json

from falcon_heavy.core.utils import comma_delimited

from .base import AbstractConvertible, BaseType, TypeMeta, ValidationResult, Messages, Types
from .enums import ConvertibleEntity
from .exceptions import SchemaError, UndefinedResultError
from .errors import Error
from .path import Path
from .undefined import Undefined

__all__ = (
    'Object',
    'Properties',
    'Required',
    'PatternProperties',
    'AdditionalProperties',
    'ReadOnly',
    'WriteOnly',
    'ObjectTypeMeta',
    'ObjectType',
)

T = ty.TypeVar('T', bound='Object')


class Object(ChainMap):

    def __init__(
            self,
            properties: ty.Optional[ty.MutableMapping[str, ty.Any]] = None,
            pattern_properties: ty.Optional[ty.MutableMapping[str, ty.Any]] = None,
            additional_properties: ty.Optional[ty.MutableMapping[str, ty.Any]] = None
    ) -> None:
        super(Object, self).__init__(
            properties or {},
            pattern_properties or {},
            additional_properties or {}
        )

    @property
    def properties(self) -> ty.MutableMapping[str, ty.Any]:
        return ty.cast(ty.MutableMapping[str, ty.Any], self.maps[0])

    @property
    def pattern_properties(self) -> ty.MutableMapping[str, ty.Any]:
        return ty.cast(ty.MutableMapping[str, ty.Any], self.maps[1])

    @property
    def additional_properties(self) -> ty.MutableMapping[str, ty.Any]:
        return ty.cast(ty.MutableMapping[str, ty.Any], self.maps[2])

    def __delitem__(self, key: str) -> None:
        did_delete = False
        for mapping in self.maps:
            try:
                del ty.cast(ty.MutableMapping, mapping)[key]
                did_delete = True
            except KeyError:
                pass
        if not did_delete:
            raise KeyError(key)

    def __or__(self: T, other: Mapping) -> T:
        if not isinstance(other, Mapping):
            raise NotImplementedError()

        if isinstance(other, Object):
            for l, r in zip(self.maps, other.maps):
                ty.cast(ty.MutableMapping, l).update(r)
        else:
            self.additional_properties.update(other)

        for key in self.properties:
            self.pattern_properties.pop(key, None)
            self.additional_properties.pop(key, None)

        for key in self.pattern_properties:
            self.additional_properties.pop(key, None)

        return self

    def __hash__(self) -> int:
        return hash(json.dumps(self, sort_keys=True))


Properties = ty.MutableMapping[str, AbstractConvertible]
Required = ty.Set[str]
PatternProperties = ty.MutableMapping[ty.Pattern, AbstractConvertible]
AdditionalProperties = ty.Union[bool, AbstractConvertible]
ReadOnly = ty.Set[str]
WriteOnly = ty.Set[str]


class ObjectTypeMeta(TypeMeta):

    def __new__(
            mcs,
            name: str,
            bases: ty.Tuple[type, ...],
            namespace: ty.Dict[str, ty.Any],
            *args: ty.Any,
            result_class: ty.Type[Object] = Object,
            **kwargs: ty.Any
    ) -> ty.Any:
        properties: Properties = {}
        required: Required = set()
        pattern_properties: PatternProperties = {}
        additional_properties: AdditionalProperties = True
        read_only: ReadOnly = set()
        write_only: WriteOnly = set()

        for base in reversed(bases):
            if hasattr(base, 'PROPERTIES'):
                properties.update(base.PROPERTIES)  # type: ignore

            if hasattr(base, 'REQUIRED'):
                required.update(set(base.REQUIRED))  # type: ignore

            if hasattr(base, 'PATTERN_PROPERTIES'):
                pattern_properties.update(base.PATTERN_PROPERTIES)  # type: ignore

            if hasattr(base, 'ADDITIONAL_PROPERTIES'):
                additional_properties = base.ADDITIONAL_PROPERTIES  # type: ignore

            if hasattr(base, 'READ_ONLY'):
                read_only.update(set(base.READ_ONLY))  # type: ignore

            if hasattr(base, 'WRITE_ONLY'):
                write_only.update(set(base.WRITE_ONLY))  # type: ignore

        if 'PROPERTIES' in namespace:
            properties.update(namespace['PROPERTIES'])

        if 'REQUIRED' in namespace:
            required.update(set(namespace['REQUIRED']))

        if 'PATTERN_PROPERTIES' in namespace:
            pattern_properties.update(namespace['PATTERN_PROPERTIES'])

        if 'ADDITIONAL_PROPERTIES' in namespace:
            additional_properties = namespace['ADDITIONAL_PROPERTIES']

        if 'READ_ONLY' in namespace:
            read_only.update(set(namespace['READ_ONLY']))

        if 'WRITE_ONLY' in namespace:
            write_only.update(set(namespace['WRITE_ONLY']))

        cls = super(ObjectTypeMeta, mcs).__new__(mcs, name, bases, namespace, *args, **kwargs)

        cls.PROPERTIES = properties  # type: ignore
        cls.REQUIRED = required  # type: ignore
        cls.PATTERN_PROPERTIES = pattern_properties  # type: ignore
        cls.ADDITIONAL_PROPERTIES = additional_properties  # type: ignore
        cls.READ_ONLY = read_only  # type: ignore
        cls.WRITE_ONLY = write_only  # type: ignore
        cls.RESULT_CLASS = result_class  # type: ignore

        return cls


class ObjectType(BaseType[T], metaclass=ObjectTypeMeta, result_class=Object):

    """Object type

    :param properties: is a dictionary, where each key is the name of a property and each value
        is a type used to validate that property
    :param required: by default, the properties defined by the `properties` are not required.
        However, one can provide a set of required properties using the `required`. The `required`
        takes an set of one or more strings
    :param pattern_properties: it is map from regular expressions to types. If an additional
        property matches a given regular expression, it must also validate against the
        corresponding type
    :param additional_properties: is used to control the handling of extra stuff, that is,
        properties whose names are not listed in the properties. If is `True` then possible
        any additional properties, that not listed in `properties`. If is `False` then
        additional properties not allowed. If is a `BaseType` then additional properties
        of this type are allowed. By default any additional properties are allowed
    :param read_only: Properties that may be sent as part of a response but should not be sent
        as part of the request. A property must not be listed in both `read_only` and
        `write_only` simultaneously
    :param write_only: Properties that may be sent as part of a request but should not be sent
        as part of the response. A property must not be listed in both `read_only` and
        `write_only` simultaneously
    :param min_properties: invalidate when number of properties less than specified
    :param max_properties: invalidate when number of properties more than specified
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a mapping",
        'required': "The following required properties are missed: {0}",
        'additional_properties': (
            "No unspecified properties are allowed."
            " The following unspecified properties were found: {0}"
        ),
        'min_properties': "Object must have at least {0} properties. It had only {1} properties",
        'max_properties': "Object must have no more than {0} properties. It had {1} properties",
        'read_only': "The following properties are read only: {0}",
        'write_only': "The following properties are write only: {0}"
    }

    PROPERTIES: ty.ClassVar[Properties]

    REQUIRED: ty.ClassVar[Required]

    PATTERN_PROPERTIES: ty.ClassVar[PatternProperties]

    ADDITIONAL_PROPERTIES: ty.ClassVar[AdditionalProperties]

    READ_ONLY: ty.ClassVar[ReadOnly]

    WRITE_ONLY: ty.ClassVar[WriteOnly]

    TYPES: ty.ClassVar[Types] = (Mapping, )

    RESULT_CLASS: ty.ClassVar[ty.Type[T]]

    __slots__ = (
        'properties',
        'required',
        'pattern_properties',
        'additional_properties',
        'read_only',
        'write_only',
        'min_properties',
        'max_properties'
    )

    def __init__(
            self,
            properties: ty.Optional[Properties] = None,
            required: ty.Optional[Required] = None,
            pattern_properties: ty.Optional[PatternProperties] = None,
            additional_properties: ty.Optional[AdditionalProperties] = None,
            read_only: ty.Optional[ReadOnly] = None,
            write_only: ty.Optional[WriteOnly] = None,
            min_properties: ty.Optional[int] = None,
            max_properties: ty.Optional[int] = None,
            **kwargs: ty.Any
    ) -> None:
        self.properties = dict(self.PROPERTIES, **(properties or {}))
        self.required: Required = self.REQUIRED
        if required:
            self.required = set.union(self.required, required)
        self.pattern_properties = self.PATTERN_PROPERTIES
        if pattern_properties is not None:
            self.pattern_properties = pattern_properties
        self.additional_properties = self.ADDITIONAL_PROPERTIES
        if additional_properties is not None:
            self.additional_properties = additional_properties
        self.read_only = read_only or self.READ_ONLY
        self.write_only = write_only or self.WRITE_ONLY
        if set.intersection(self.read_only, self.write_only):
            raise ValueError(
                "Properties must not be listed in both "
                "``read_only`` and ``write_only`` simultaneously"
            )
        if not set.issubset(self.read_only, set(self.properties)):
            raise ValueError("All read-only properties must be present in the properties")
        if not set.issubset(self.write_only, set(self.properties)):
            raise ValueError("All write-only properties must be present in the properties")
        self.min_properties = min_properties
        self.max_properties = max_properties
        super(ObjectType, self).__init__(**kwargs)

    def _convert(
            self,
            value: ty.Mapping,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> T:
        errors: ty.List[Error] = []
        result = self.RESULT_CLASS()

        unacceptable = []
        if entity == ConvertibleEntity.REQUEST:
            for property_name in self.read_only:
                if property_name in value:
                    unacceptable.append(property_name)

            if unacceptable:
                errors.append(Error(
                    path, self.messages['read_only'].format(comma_delimited(unacceptable))))

        elif entity == ConvertibleEntity.RESPONSE:
            for property_name in self.write_only:
                if property_name in value:
                    unacceptable.append(property_name)

            if unacceptable:
                errors.append(Error(
                    path, self.messages['write_only'].format(comma_delimited(unacceptable))))

        required = self.required
        if entity == ConvertibleEntity.REQUEST:
            required -= self.read_only

        elif entity == ConvertibleEntity.RESPONSE:
            required -= self.write_only

        missed = set()
        for property_name in required:
            if property_name not in value:
                missed.add(property_name)

        if missed:
            errors.append(Error(
                path, self.messages['required'].format(comma_delimited(missed))))

        additional_properties = set(value) - set(self.properties)
        not_matched = []
        for property_name in additional_properties:
            property_value = value[property_name]
            property_path = path / property_name
            matched = None
            for pattern, property_type in self.pattern_properties.items():
                try:
                    matched = pattern.match(property_name)
                except (TypeError, ValueError):
                    continue

                if not matched:
                    continue

                try:
                    result.pattern_properties[property_name] = property_type.convert(
                        property_value, property_path, entity=entity, **context)
                except SchemaError as e:
                    errors.extend(e.errors)

                else:
                    break

            if matched:
                continue

            if self.additional_properties is True:
                result.additional_properties[property_name] = property_value
                continue

            elif isinstance(self.additional_properties, AbstractConvertible):
                try:
                    result.additional_properties[property_name] = self.additional_properties.convert(
                        property_value, property_path, entity=entity, **context)
                except SchemaError as e:
                    errors.extend(e.errors)
                else:
                    continue

            not_matched.append(property_name)

        if not_matched:
            errors.append(Error(
                path, self.messages['additional_properties'].format(comma_delimited(not_matched))))

        for property_name, property_type in self.properties.items():
            if property_name in missed:
                continue

            if entity == ConvertibleEntity.REQUEST and property_name in self.read_only:
                continue

            if entity == ConvertibleEntity.RESPONSE and property_name in self.write_only:
                continue

            try:
                result.properties[property_name] = property_type.convert(
                    value.get(property_name, Undefined), path / property_name, entity=entity, **context)
            except SchemaError as e:
                errors.extend(e.errors)
                continue

            except UndefinedResultError:
                continue

        if errors:
            raise SchemaError(*errors)

        return result

    def validate_length(
            self, value: ty.Any, original: ty.Mapping, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        length = len(original)

        if self.min_properties is not None and length < self.min_properties:
            return self.messages['min_properties'].format(self.min_properties, length)

        if self.max_properties is not None and length > self.max_properties:
            return self.messages['max_properties'].format(self.max_properties, length)

        return None
