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
from distutils.util import strtobool

from falcon_heavy.utils import force_str, FalconHeavyUnicodeDecodeError

from .base import BaseType, ValidationResult, Messages, Types
from .path import Path
from .exceptions import SchemaError
from .errors import Error

__all__ = (
    'StringType',
    'Number',
    'GenericNumberType',
    'NumberType',
    'IntegerType',
    'BooleanType',
)


class StringType(BaseType[str]):

    """String type

    :param min_length: invalidate when value length less than specified
    :param max_length: invalidate when value length greater than specified
    :param pattern: invalidate when value is not match to specified pattern
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a string",
        'cast': "Couldn't cast to a string",
        'min_length': "Must be no less than {0} characters in length",
        'max_length': "Must be no greater than {0} characters in length",
        'pattern': "Does not match the pattern"
    }

    TYPES: ty.ClassVar[Types] = (str, )

    __slots__ = (
        'min_length',
        'max_length',
        'pattern'
    )

    def __init__(
            self,
            min_length: ty.Optional[int] = None,
            max_length: ty.Optional[int] = None,
            pattern: ty.Optional[ty.Pattern] = None,
            **kwargs: ty.Any
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        super(StringType, self).__init__(**kwargs)

    def _cast(self, value: ty.Any, path: Path, *args: ty.Any, strict: bool = True, **context: ty.Any) -> ty.Any:
        if isinstance(value, self.TYPES) or strict:
            return value

        try:
            return force_str(value, errors='replace')
        except FalconHeavyUnicodeDecodeError:
            raise SchemaError(Error(path, self.messages['cast']))

    def validate_length(self, value: str, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if self.min_length is not None and len(value) < self.min_length:
            return self.messages['min_length'].format(self.min_length)

        if self.max_length is not None and len(value) > self.max_length:
            return self.messages['max_length'].format(self.max_length)

        return None

    def validate_pattern(self, value: str, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if self.pattern is not None and self.pattern.match(value) is None:
            return self.messages['pattern']

        return None


Number = ty.Union[int, float]

T_num = ty.TypeVar('T_num', int, float, Number)


class GenericNumberType(BaseType[T_num]):

    """Generic number type

    :param minimum: invalidate when value less than specified minimum
    :param maximum: Invalidate when value greater than specified maximum
    :param exclusive_minimum: when True, it indicates that the range excludes the minimum value.
        When False (or not included), it indicates that the range includes the minimum value
    :param exclusive_maximum: when True, it indicates that the range excludes the maximum value.
        When false (or not included), it indicates that the range includes the maximum value
    :param multiple_of: invalidate when value is not multiple of specified
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a number",
        'cast': "Couldn't cast to a number",
        'minimum': "Is less than the minimum of {0}",
        'exclusive_minimum': "Is less than or equal to the minimum of {0}",
        'maximum': "Is greater than the maximum of {0}",
        'exclusive_maximum': "Is greater than or equal to the maximum of {0}",
        'multiple_of': "Is not a multiple of {0}"
    }

    TYPES: ty.ClassVar[Types] = (int, float)

    __slots__ = (
        'minimum',
        'maximum',
        'exclusive_minimum',
        'exclusive_maximum',
        'multiple_of'
    )

    def __init__(
            self,
            minimum: ty.Optional[Number] = None,
            maximum: ty.Optional[Number] = None,
            exclusive_minimum: bool = False,
            exclusive_maximum: bool = False,
            multiple_of: ty.Optional[Number] = None,
            **kwargs: ty.Any
    ) -> None:
        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of
        super(GenericNumberType, self).__init__(**kwargs)

    def _cast(self, value: ty.Any, path: Path, *args: ty.Any, strict: bool = True, **context: ty.Any) -> ty.Any:
        if isinstance(value, self.TYPES) or strict:
            return value

        if isinstance(value, bool):
            return int(value)

        try:
            return float(value)
        except (ValueError, TypeError):
            raise SchemaError(Error(path, self.messages['cast']))

    def _check_type(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> bool:
        # bool is subtype of int
        if isinstance(value, bool):
            return False

        return super(GenericNumberType, self)._check_type(value, path, **context)

    def validate_minimum(self, value: Number, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if self.minimum is None:
            return None

        if self.exclusive_minimum and value <= self.minimum:
            return self.messages['exclusive_minimum'].format(self.minimum)

        if not self.exclusive_minimum and value < self.minimum:
            return self.messages['minimum'].format(self.minimum)

        return None

    def validate_maximum(self, value: Number, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if self.maximum is None:
            return None

        if self.exclusive_maximum and value >= self.maximum:
            return self.messages['exclusive_maximum'].format(self.maximum)

        if not self.exclusive_maximum and value > self.maximum:
            return self.messages['maximum'].format(self.maximum)

        return None

    def validate_multiple_of(self, value: Number, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if self.multiple_of is None:
            return None

        if isinstance(self.multiple_of, float):
            quotient = value / self.multiple_of
            failed = int(quotient) != quotient

        else:
            failed = value % self.multiple_of

        if failed:
            return self.messages['multiple_of'].format(self.multiple_of)

        return None


class NumberType(GenericNumberType[Number]):

    """Number type"""


class IntegerType(GenericNumberType[int]):

    """Integer type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be an integer",
        'cast': "Couldn't cast to an integer"
    }

    TYPES: ty.ClassVar[Types] = (int, )

    __slots__ = ()

    def _cast(self, value: ty.Any, path: Path, *args: ty.Any, strict: bool = True, **context: ty.Any) -> ty.Any:
        if isinstance(value, self.TYPES) or strict:
            return value

        try:
            return int(value)
        except (TypeError, ValueError):
            raise SchemaError(Error(path, self.messages['cast']))


class BooleanType(BaseType[bool]):

    """Boolean type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a boolean",
        'cast': "Couldn't cast to a boolean"
    }

    TYPES: ty.ClassVar[Types] = (bool, )

    __slots__ = ()

    def _cast(self, value: ty.Any, path: Path, *args: ty.Any, strict: bool = True, **context: ty.Any) -> ty.Any:
        if isinstance(value, self.TYPES) or strict:
            return value

        if isinstance(value, str):
            try:
                return bool(strtobool(value))
            except ValueError:
                pass

        elif isinstance(value, (int, float)):
            return bool(value)

        raise SchemaError(Error(path, self.messages['cast']))
