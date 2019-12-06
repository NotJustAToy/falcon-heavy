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
from functools import lru_cache
from urllib.parse import urldefrag

__all__ = (
    'Parts',
    'Path',
)

_urldefrag_cache = lru_cache(1024)(urldefrag)


def _escape(s: str) -> str:
    return s.replace('~', '~0').replace('/', '~1')


T = ty.TypeVar('T', bound='Path')
Parts = ty.Tuple[str, ...]


class Path:

    __slots__ = (
        '_url',
        '_parts'
    )

    _url: str
    _parts: Parts

    def __new__(cls: ty.Type[T], uri: ty.Optional[str] = None) -> T:
        return cls._from_uri(uri or '')

    @classmethod
    def _from_uri(cls: ty.Type[T], uri: str) -> T:
        self = object.__new__(cls)
        url, fragment = _urldefrag_cache(uri)
        self._url = url
        self._parts = tuple(filter(None, fragment.split('/')))
        return self

    @classmethod
    def _from_parsed_parts(cls: ty.Type[T], url: str, parts: Parts) -> T:
        self = object.__new__(cls)
        self._url = url
        self._parts = parts
        return self

    def _make_child(self, part: str) -> 'Path':
        return self._from_parsed_parts(self._url, self._parts + (part, ))

    @property
    def parent(self) -> 'Path':
        if not self._parts:
            return self

        return self._from_parsed_parts(self._url, self._parts[:-1])

    @property
    def parts(self) -> Parts:
        return self._parts

    @property
    def url(self) -> str:
        return self._url

    def __div__(self: T, part: ty.Any) -> 'Path':
        if isinstance(part, int):
            part = str(part)

        elif not isinstance(part, str):
            raise NotImplementedError()

        return self._make_child(part)

    __truediv__ = __div__

    def __eq__(self, other: ty.Any) -> bool:
        if isinstance(other, str):
            return str(self) == other

        elif isinstance(other, Path):
            return self.url == other.url and self.parts == other.parts

        else:
            raise NotImplementedError()

    def __lt__(self, other: ty.Any) -> bool:
        if isinstance(other, str):
            return str(self) < other

        elif isinstance(other, Path):
            return str(self) < str(other)

        else:
            raise NotImplementedError()

    def __gt__(self, other: ty.Any) -> bool:
        if isinstance(other, str):
            return str(self) > other

        elif isinstance(other, Path):
            return str(self) > str(other)

        else:
            raise NotImplementedError()

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        fragment = '/'.join(map(_escape, self._parts))

        if fragment:
            return '#/'.join((self._url, fragment))
        elif self._url:
            return self._url
        else:
            return '#'

    def __repr__(self) -> str:
        return "%s(%r)" % (self.__class__.__name__, str(self))
