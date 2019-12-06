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

import operator
import typing as ty
from collections import Mapping
from functools import reduce

from falcon_heavy.core.utils import comma_delimited

from .base import AbstractConvertible, BaseType, Messages, Types
from .object import Object
from .exceptions import SchemaError
from .errors import Error
from .path import Path

__all__ = (
    'DiscriminatedType',
    'AllOfType',
    'AnyOfType',
    'OneOfType',
    'NotType',
)


class DiscriminatedType(BaseType):

    """Discriminated type

    :param property_name: property name that decides target type
    :param mapping: mapping of extracted values to target types
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a mapping",
        'not_present': "A property with name '{0}' must be present",
        'not_match': "The discriminator value must be equal to one of the following values: {0}"
    }

    TYPES: ty.ClassVar[Types] = (Mapping, )

    __slots__ = (
        'property_name',
        'mapping'
    )

    def __init__(
            self,
            property_name: str,
            mapping: ty.Mapping[str, AbstractConvertible],
            **kwargs: ty.Any
    ) -> None:
        self.property_name = property_name
        self.mapping = mapping
        super(DiscriminatedType, self).__init__(**kwargs)

    def _convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        if self.property_name not in value:
            raise SchemaError(Error(path, self.messages['not_present'].format(self.property_name)))

        matched_type = self.mapping.get(value[self.property_name])

        if matched_type is None:
            raise SchemaError(Error(
                path, self.messages['not_match'].format(comma_delimited(self.mapping.keys()))))

        return matched_type.convert(value, path, **context)


class AllOfType(BaseType):

    """AllOf type

    The given data must be valid against all of the given subschemas

    :param subtypes: types for which the given data must be valid
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'not_all': "Does not match all schemas from `allOf`. Invalid schema indexes: {0}"
    }

    __slots__ = ('subtypes', )

    def __init__(self, subtypes: ty.Iterable[AbstractConvertible], **kwargs: ty.Any) -> None:
        self.subtypes = subtypes
        super(AllOfType, self).__init__(**kwargs)

    def _convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        matched: ty.List[ty.Any] = []
        not_matched_indexes: ty.List[int] = []
        errors: ty.List[Error] = []
        for i, subtype in enumerate(self.subtypes):
            try:
                matched.append(subtype.convert(value, path / i, **context))
            except SchemaError as e:
                errors.extend(e.errors)
                not_matched_indexes.append(i)
                continue

        if errors:
            raise SchemaError(
                Error(path, self.messages['not_all'].format(comma_delimited(not_matched_indexes))), *errors)

        if all(isinstance(value, Mapping) for value in matched):
            matched.insert(0, Object())
            return reduce(operator.or_, matched)

        if all(isinstance(value, (list, tuple)) for value in matched):
            result: ty.List = []
            for squashed in zip(matched):
                if all(isinstance(value, Mapping) for value in squashed):
                    result.append(reduce(operator.or_, (Object(),) + squashed))
                else:
                    result.append(squashed[-1])
            return result

        return matched[-1]


class AnyOfType(BaseType):

    """AnyOf type

    The given data must be valid against any (one or more) of the given subschemas

    :param subtypes: types for which the given data must be valid
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'not_any': "Does not match any schemas from `anyOf`"
    }

    __slots__ = ('subtypes', )

    def __init__(self, subtypes: ty.Iterable[AbstractConvertible], **kwargs: ty.Any) -> None:
        self.subtypes = subtypes
        super(AnyOfType, self).__init__(**kwargs)

    def _convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        matched = None
        errors: ty.List[Error] = []
        for i, subtype in enumerate(self.subtypes):
            try:
                matched = subtype.convert(value, path / i, **context)
            except SchemaError as e:
                errors.extend(e.errors)
                continue
            else:
                break

        if matched is None:
            raise SchemaError(Error(path, self.messages['not_any']), *errors)

        return matched


class OneOfType(BaseType):

    """OneOf type

    The given data must be valid against exactly one of the given subschemas

    :param subtypes: types for which the given data must be valid
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'no_one': "Is valid against no schemas from `oneOf`",
        'ambiguous': "Is valid against more than one schema from `oneOf`. Valid schema indexes: {0}"
    }

    __slots__ = ('subtypes', )

    def __init__(self, subtypes: ty.Iterable[AbstractConvertible], **kwargs: ty.Any) -> None:
        self.subtypes = subtypes
        super(OneOfType, self).__init__(**kwargs)

    def _convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        matched: ty.List[ty.Any] = []
        matched_indexes: ty.List[int] = []
        errors: ty.List[Error] = []
        for i, subtype in enumerate(self.subtypes):
            try:
                matched.append(subtype.convert(value, path / i, **context))
                matched_indexes.append(i)
            except SchemaError as e:
                errors.extend(e.errors)

        if not matched:
            raise SchemaError(Error(path, self.messages['no_one']), *errors)

        elif len(matched) > 1:
            raise SchemaError(Error(path, self.messages['ambiguous'].format(comma_delimited(matched_indexes))))

        return matched[0]


class NotType(BaseType):

    """Not type

    Declares that a instance validates if it doesn't validate against the given subschemas

    :param subtypes: types for which the given data must not be valid
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'not_acceptable': "Not acceptable data"
    }

    __slots__ = ('subtypes', )

    def __init__(self, subtypes: ty.Iterable[AbstractConvertible], **kwargs: ty.Any) -> None:
        self.subtypes = subtypes
        super(NotType, self).__init__(**kwargs)

    def _convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        for i, subtype in enumerate(self.subtypes):
            try:
                subtype.convert(value, path / i, **context)
            except SchemaError:
                pass
            else:
                raise SchemaError(Error(path, self.messages['not_acceptable']))

        return value
