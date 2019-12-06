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
from collections import Mapping

import mimeparse

from falcon_heavy.core import types as t
from falcon_heavy.core.utils import comma_delimited

__all__ = (
    'SingleEntryMapType',
    'ContentTypeBestMatchedType',
    'ResponseCodeBestMatchedType',
)

T = ty.TypeVar('T')


class SingleEntryMapType(t.BaseType[ty.Mapping[str, T]]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'type': "Must be a mapping",
        'length': "Must contains only one entry"
    }

    TYPES: ty.ClassVar[t.Types] = (Mapping, )

    __slots__ = ()

    def validate_length(self, value: ty.Mapping[str, T], *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if len(value) != 1:
            return self.messages['length']

        return None


class AbstractBestMatchedType(t.AbstractConvertible[T]):

    __slots__ = ('subtype', 'allowed', )

    def __init__(
            self,
            subtype: SingleEntryMapType[T],
            allowed: ty.Mapping[str, t.AbstractConvertible[T]],
            **kwargs: ty.Any
    ) -> None:
        super(AbstractBestMatchedType, self).__init__(**kwargs)
        self.subtype = subtype
        self.allowed = allowed

    def _get_best_matched(self, key: str) -> ty.Optional[t.AbstractConvertible[T]]:
        raise NotImplementedError()

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[T]:
        result = self.subtype.convert(value, path, *args, **context)

        if result is None:
            return None

        k, v = next(iter(value.items()))
        best = self._get_best_matched(k)

        if best is None:
            raise t.SchemaError(t.Error(path, self.messages['unallowed'].format(
                k, comma_delimited(self.allowed))))

        return best.convert(v, path, **context)


class ContentTypeBestMatchedType(AbstractBestMatchedType[T]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'unallowed': "Not allowed content type '{0}'. Must be one of: {1}."
    }

    __slots__ = ()

    def _get_best_matched(self, key: str) -> ty.Optional[t.AbstractConvertible[T]]:
        best = self.allowed.get(key)

        if best is None:
            match = mimeparse.best_match(self.allowed.keys(), key)
            if match:
                best = self.allowed[match]

        return best


class ResponseCodeBestMatchedType(AbstractBestMatchedType[T]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'unallowed': (
            "Request status code was not found in the known response codes. Got: {0}. "
            "Expected one of: {1}"
        )
    }

    __slots__ = ('reduced', )

    def __init__(
            self,
            subtype: SingleEntryMapType[T],
            allowed: ty.Mapping[str, t.AbstractConvertible[T]],
            **kwargs: ty.Any
    ) -> None:
        super(ResponseCodeBestMatchedType, self).__init__(subtype, allowed, **kwargs)
        self.reduced = {k.lower().replace('x', ''): v for k, v in self.allowed.items()}

    def _get_best_matched(self, key: str) -> ty.Optional[t.AbstractConvertible[T]]:
        default = self.allowed.get('default', None)
        key = str(key)

        best = self.allowed.get(key)

        if best is None and key:
            best = self.reduced.get(key[0])

        if best is None and default is not None:
            best = default

        return best
