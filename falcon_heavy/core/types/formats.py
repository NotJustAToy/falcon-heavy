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

import io
import re
import uuid
import base64
import binascii
import datetime
import typing as ty

import rfc3987
import rfc3339

from strict_rfc3339 import rfc3339_to_timestamp, InvalidRFC3339Error

from falcon_heavy.utils import force_str, force_bytes

from .base import AbstractConvertible, BaseType, ValidationResult, Messages
from .primitive import StringType, IntegerType
from .enums import ConvertibleEntity
from .exceptions import SchemaError
from .errors import Error
from .path import Path
from .utils import is_file_like

__all__ = (
    'DateType',
    'DateTimeType',
    'RegexType',
    'URIType',
    'EmailType',
    'Int32Type',
    'Int64Type',
    'UUIDType',
    'ByteType',
    'BinaryType',
)


class DateType(AbstractConvertible[ty.Union[str, datetime.date]]):

    """Date type

    Converts RFC3339 full-date string into python date object and vice versa

    :param subtype: basic converter
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid RFC3339 full-date"
    }

    __slots__ = ('subtype', )

    def __init__(self, subtype: StringType, **kwargs: ty.Any) -> None:
        super(DateType, self).__init__(**kwargs)
        self.subtype = subtype

    def convert(
            self,
            value: ty.Any,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Optional[ty.Union[str, datetime.date]]:
        if isinstance(value, datetime.date) and entity == ConvertibleEntity.RESPONSE and value is not None:
            value = value.isoformat()

        result = self.subtype.convert(value, path, *args, entity=entity, **context)

        if entity == ConvertibleEntity.RESPONSE:
            return result

        if result is None:
            return None

        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise SchemaError(Error(path, self.messages['format']))


class DateTimeType(AbstractConvertible[ty.Union[str, datetime.datetime]]):

    """Datetime type

    Converts RFC3339 date-time string into python datetime object and vice versa

    :param subtype: basic converter
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid RFC3339 date-time"
    }

    __slots__ = ('subtype', )

    def __init__(self, subtype: StringType, **kwargs: ty.Any) -> None:
        super(DateTimeType, self).__init__(**kwargs)
        self.subtype = subtype

    def convert(
            self,
            value: ty.Any,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Optional[ty.Union[str, datetime.datetime]]:
        if isinstance(value, datetime.datetime) and entity == ConvertibleEntity.RESPONSE and value is not None:
            value = rfc3339.rfc3339(value)

        result = self.subtype.convert(value, path, *args, entity=entity, **context)

        if entity == ConvertibleEntity.RESPONSE:
            return result

        if result is None:
            return None

        try:
            return datetime.datetime.fromtimestamp(rfc3339_to_timestamp(value))
        except InvalidRFC3339Error:
            raise SchemaError(Error(path, self.messages['format']))


class RegexType(AbstractConvertible[ty.Union[str, ty.Pattern]]):

    """Regex type

    :param subtype: basic converter
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid regular expression"
    }

    __slots__ = ('subtype', )

    def __init__(self, subtype: StringType, **kwargs: ty.Any) -> None:
        super(RegexType, self).__init__(**kwargs)
        self.subtype = subtype

    def convert(
            self,
            value: ty.Any,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Optional[ty.Union[str, ty.Pattern]]:
        result = self.subtype.convert(value, path, *args, entity=entity, **context)

        if entity == ConvertibleEntity.RESPONSE:
            return result

        if result is None:
            return None

        try:
            return re.compile(result)
        except (TypeError, re.error):
            raise SchemaError(Error(path, self.messages['format']))


class URIType(StringType):

    """URI type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid URI according to RFC3987"
    }

    __slots__ = ()

    def validate_format(self, value: str, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        try:
            rfc3987.parse(value, rule='URI')
        except ValueError:
            return self.messages['format']

        return None


EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


class EmailType(StringType):

    """Email type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid email address according to RFC5322"
    }

    __slots__ = ()

    def validate_format(self, value: str, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if not EMAIL_PATTERN.match(value):
            return self.messages['format']

        return None


class Int32Type(IntegerType):

    """Int32 type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid Int32"
    }

    __slots__ = ()

    def validate_format(self, value: int, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if value < -2147483648 or value > 2147483647:
            return self.messages['format']

        return None


class Int64Type(IntegerType):

    """Int64 type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid Int64"
    }

    __slots__ = ()

    def validate_format(self, value: int, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if value < -9223372036854775808 or value > 9223372036854775807:
            return self.messages['format']

        return None


UUID_PATTERN = re.compile(
    '^'
    '[a-f0-9]{8}-'
    '[a-f0-9]{4}-'
    '[1345][a-f0-9]{3}-'
    '[a-f0-9]{4}'
    '-[a-f0-9]{12}'
    '$'
)


class UUIDType(StringType):

    """UUID type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not a valid UUID"
    }

    __slots__ = ()

    def _cast(
            self,
            value: ty.Any,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Any:
        if entity == ConvertibleEntity.RESPONSE and isinstance(value, uuid.UUID):
            return str(value)

        return value

    def validate_format(self, value: str, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if not UUID_PATTERN.match(value):
            return self.messages['format']

        return None


class ByteType(AbstractConvertible[ty.Union[str, ty.BinaryIO]]):

    """Byte type

    :param subtype: basic converter
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'format': "Is not base64 encoded"
    }

    __slots__ = ('subtype', )

    def __init__(self, subtype: StringType, **kwargs: ty.Any) -> None:
        super(ByteType, self).__init__(**kwargs)
        self.subtype = subtype

    def convert(
            self,
            value: ty.Any,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Optional[ty.Union[str, ty.BinaryIO]]:
        if entity == ConvertibleEntity.RESPONSE and value is not None:
            value = force_str(base64.b64encode(force_bytes(value)), encoding='ascii')

        result = self.subtype.convert(value, path, *args, entity=entity, **context)

        if entity == ConvertibleEntity.REQUEST and result is not None:
            try:
                return io.BytesIO(base64.b64decode(result, validate=True))
            except binascii.Error:
                raise SchemaError(Error(path, self.messages['format']))

        return result


class BinaryType(BaseType[ty.IO]):

    """Binary type"""

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Must be a file-like object"
    }

    __slots__ = ()

    def _check_type(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> bool:
        return is_file_like(value)
