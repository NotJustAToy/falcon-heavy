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

from mypy_extensions import Arg, VarArg, KwArg

from falcon_heavy.core.utils import comma_delimited

from .enums import ConvertibleEntity
from .exceptions import SchemaError, UndefinedResultError
from .errors import Error
from .path import Path
from .undefined import Undefined

__all__ = (
    'Messages',
    'OverridableMessagesMeta',
    'AbstractConvertible',
    'ValidationResult',
    'AbstractValidator',
    'TypeMeta',
    'Validator',
    'DefaultValue',
    'Types',
    'BaseType',
)

Messages = ty.MutableMapping[str, str]


try:
    from typing import GenericMeta  # python 3.6
except ImportError:
    # in 3.7, GenericMeta doesn't exist but we don't need it
    class GenericMeta(type):  # type: ignore
        pass


class OverridableMessagesMeta(GenericMeta):

    def __new__(
            mcs,
            name: str,
            bases: ty.Tuple[type, ...],
            namespace: ty.Dict[str, ty.Any],
            *args: ty.Any,
            **kwargs: ty.Any
    ) -> ty.Any:
        messages: Messages = {}

        for base in reversed(bases):
            if hasattr(base, 'MESSAGES'):
                messages.update(base.MESSAGES)  # type: ignore

        if 'MESSAGES' in namespace:
            messages.update(namespace['MESSAGES'])

        cls = super(OverridableMessagesMeta, mcs).__new__(mcs, name, bases, namespace, *args, **kwargs)  # type: ignore
        cls.MESSAGES = messages  # type: ignore

        return cls


class _Base:

    __slots__ = ('__weakref__', )


T = ty.TypeVar('T')


class AbstractConvertible(_Base, ty.Generic[T], metaclass=OverridableMessagesMeta):

    MESSAGES: ty.ClassVar[Messages]

    __slots__ = ('messages', )

    def __init__(self, messages: ty.Optional[Messages] = None) -> None:
        self.messages = dict(self.MESSAGES, **(messages or {}))

    def convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[T]:
        raise NotImplementedError()


ValidationResult = ty.Optional[str]


class AbstractValidator(_Base, ty.Generic[T], metaclass=OverridableMessagesMeta):

    MESSAGES: ty.ClassVar[Messages]

    __slots__ = ('messages', )

    def __init__(self, messages: ty.Optional[Messages] = None) -> None:
        self.messages = dict(self.MESSAGES, **(messages or {}))

    def __call__(self, value: T, original: ty.Any, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        raise NotImplementedError()


class TypeMeta(OverridableMessagesMeta):

    def __new__(
            mcs,
            name: str,
            bases: ty.Tuple[type, ...],
            namespace: ty.Dict[str, ty.Any],
            *args: ty.Any,
            **kwargs: ty.Any
    ) -> ty.Any:
        validators: ty.Set[str] = set()

        for base in reversed(bases):
            if hasattr(base, "VALIDATORS"):
                validators.update(base.VALIDATORS)  # type: ignore

        for attr_name, attr in namespace.items():
            if attr_name.startswith('validate_'):
                validators.add(attr_name)

        cls = super(TypeMeta, mcs).__new__(mcs, name, bases, namespace, *args, **kwargs)
        cls.VALIDATORS = validators  # type: ignore

        return cls


Validator = ty.Union[
    ty.Callable[
        [Arg(T, 'value'), Arg(ty.Any, 'original'), VarArg(ty.Any), KwArg(ty.Any)],
        ValidationResult
    ],
    AbstractValidator[T]
]
DefaultValue = ty.Union[ty.Any, ty.Callable[[], ty.Any]]
Types = ty.Tuple[type, ...]


class BaseType(AbstractConvertible[T], metaclass=TypeMeta):

    """Base type

    :param default: default value
    :param nullable: invalidate when value is None
    :param enum: determines allowed values
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'type': "Unexpected type",
        'nullable': "Null values not allowed",
        'enum': "Must be equal to one of the following values: {0}"
    }

    TYPES: ty.ClassVar[Types] = ()

    VALIDATORS: ty.ClassVar[ty.Set[str]]

    __slots__ = (
        '_default',
        'nullable',
        'enum',
        'validators'
    )

    def __init__(
            self,
            default: DefaultValue = Undefined,
            nullable: bool = False,
            enum: ty.Optional[ty.Iterable] = None,
            validators: ty.Optional[ty.Iterable[Validator[T]]] = None,
            **kwargs: ty.Any
    ) -> None:
        self._default = default
        self.nullable = nullable
        self.enum = enum
        self.validators: ty.List[Validator[T]] = [getattr(self, validator_name) for validator_name in self.VALIDATORS]
        if validators:
            self.validators.extend(validators)
        super(BaseType, self).__init__(**kwargs)

    @property
    def default(self) -> ty.Any:
        if callable(self._default):
            return self._default()

        return self._default

    def _cast(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        return value

    def _check_type(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> bool:
        return not self.TYPES or isinstance(value, self.TYPES)

    def _convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> T:
        return value

    def _validate(self, value: T, original: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> None:
        errors = []
        for validator in self.validators:
            message = validator(value, original, **context)
            if message is not None:
                errors.append(Error(path, message))

        if errors:
            raise SchemaError(*errors)

    def convert(
            self,
            value: ty.Any,
            path: Path,
            *args: ty.Any,
            entity: ty.Optional[ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Optional[T]:
        if not self.nullable and value is None:
            raise SchemaError(Error(path, self.messages['nullable']))

        if value is None:
            return None

        if value is Undefined:
            # Not provide default value at response
            if entity == ConvertibleEntity.RESPONSE:
                raise UndefinedResultError()

            default = self.default

            if default is Undefined:
                raise UndefinedResultError()
            else:
                value = default

        value = original = self._cast(
            value, path, entity=entity, **context)

        if not self._check_type(value, path, entity=entity, **context):
            raise SchemaError(Error(path, self.messages['type']))

        result = self._convert(value, path, entity=entity, **context)

        self._validate(result, original, path, entity=entity, **context)

        return result

    def validate_enum(self, value: ty.Any, *args: ty.Any, **context: ty.Any) -> ValidationResult:
        if self.enum and value not in self.enum:
            return self.messages['enum'].format(comma_delimited(self.enum))

        return None
