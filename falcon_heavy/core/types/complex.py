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
from collections import Mapping

from falcon_heavy.utils import force_str, FalconHeavyUnicodeDecodeError

from .base import AbstractConvertible, BaseType, ValidationResult, Messages, Types
from .enums import ConvertibleEntity
from .exceptions import SchemaError
from .errors import Error
from .path import Path
from .utils import uniq

__all__ = (
    'ArrayType',
    'MapType',
)

T_item = ty.TypeVar('T_item')


class ArrayType(BaseType[ty.Sequence[ty.Optional[T_item]]]):

    """Array type

    :param item_type: type of items
    :param min_items: invalidate when value length less than specified
    :param max_items: invalidate when value length more than specified
    :param unique_items: shows that each of the items in an array must be unique
    :param unique_item_properties: allows to check that some properties in array items are unique
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a list or a tuple",
        'min_items': "Array must have at least {0} items. It had only {1} items",
        'max_items': "Array must have no more than {0} items. It had {1} items",
        'unique_items': "Has non-unique items",
        'unique_item_properties': "All items must be a mapping"
    }

    TYPES: ty.ClassVar[Types] = (list, tuple)

    __slots__ = (
        'item_type',
        'min_items',
        'max_items',
        'unique_items',
        'unique_item_properties'
    )

    def __init__(
            self,
            item_type: AbstractConvertible[T_item],
            min_items: ty.Optional[int] = None,
            max_items: ty.Optional[int] = None,
            unique_items: bool = False,
            unique_item_properties: ty.Optional[ty.Iterable[str]] = None,
            **kwargs: ty.Any
    ) -> None:
        self.item_type = item_type
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items
        self.unique_item_properties = unique_item_properties
        super(ArrayType, self).__init__(**kwargs)

    def _convert(
            self,
            value: ty.Union[list, tuple],
            path: Path,
            *args: ty.Any,
            **context: ty.Any
    ) -> ty.Sequence[ty.Optional[T_item]]:
        result = []
        errors: ty.List[Error] = []
        for i, item in enumerate(value):
            try:
                result.append(self.item_type.convert(item, path / i, **context))
            except SchemaError as e:
                errors.extend(e.errors)

        if errors:
            raise SchemaError(*errors)

        return result

    def validate_length(self, value: ty.Sized, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        length = len(value)

        if self.min_items is not None and length < self.min_items:
            return self.messages['min_items'].format(self.min_items, length)

        if self.max_items is not None and length > self.max_items:
            return self.messages['max_items'].format(self.max_items, length)

        return None

    def validate_uniqueness(self, value: ty.Sequence, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if not self.unique_items:
            return None

        items = value
        if self.unique_item_properties:
            if not all(isinstance(item, Mapping) for item in value):
                return self.messages['unique_item_properties']

            items = [tuple(item.get(k) for k in self.unique_item_properties) for item in value]

        if not uniq(items):
            return self.messages['unique_items']

        return None


T_value = ty.TypeVar('T_value')


class MapType(BaseType[ty.Mapping[str, ty.Optional[T_value]]]):

    """Map type

    :param value_type: type of map values
    :param min_values: invalidate when number of values less than specified
    :param max_values: invalidate when number of values more than specified
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a mapping",
        'key_convert': "Couldn't convert key '{0}' to a string",
        'min_values': "Map must have at least {0} values. It had only {1} values",
        'max_values': "Map must have no more than {0} values. It had {1} values",
    }

    TYPES: ty.ClassVar[Types] = (Mapping, )

    __slots__ = (
        'value_type',
        'min_values',
        'max_values'
    )

    def __init__(
            self,
            value_type: AbstractConvertible[T_value],
            min_values: ty.Optional[int] = None,
            max_values: ty.Optional[int] = None,
            **kwargs: ty.Any
    ) -> None:
        self.value_type = value_type
        self.min_values = min_values
        self.max_values = max_values
        super(MapType, self).__init__(**kwargs)

    def _convert(
            self,
            value: Mapping,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Mapping[str, ty.Optional[T_value]]:
        result = {}
        errors: ty.List[Error] = []
        for k, v in sorted(value.items()):
            if entity == ConvertibleEntity.SPECIFICATION:
                try:
                    k = force_str(k, errors='strict')
                except FalconHeavyUnicodeDecodeError:
                    errors.append(Error(path, self.messages['key_convert'].format(k)))

            try:
                result[k] = self.value_type.convert(
                    v, path / k, entity=entity, **context)
            except SchemaError as e:
                errors.extend(e.errors)

        if errors:
            raise SchemaError(*errors)

        return result

    def validate_length(self, value: ty.Mapping, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        length = len(value)

        if self.min_values is not None and length < self.min_values:
            return self.messages['min_values'].format(self.min_values, length)

        if self.max_values is not None and length > self.max_values:
            return self.messages['max_values'].format(self.max_values, length)

        return None
