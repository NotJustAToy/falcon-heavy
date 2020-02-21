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

from falcon_heavy.utils import cached_property

from .base import AbstractConvertible, BaseType
from .path import Path

__all__ = (
    'AnyType',
    'LazyType',
)


class AnyType(BaseType):

    """Any type"""

    __slots__ = ()


T = ty.TypeVar('T')


class LazyType(AbstractConvertible[T]):

    """Lazy type

    Resolves target type when it needed

    :param resolver: callable for lazy resolving of target type
    """

    def __init__(self, resolver: ty.Callable[[], AbstractConvertible[T]], **kwargs: ty.Any) -> None:
        self.resolver = resolver
        super(LazyType, self).__init__(**kwargs)

    @cached_property
    def resolved(self) -> AbstractConvertible[T]:
        return self.resolver()

    def convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> ty.Optional[T]:
        return self.resolved.convert(value, path, **context)
