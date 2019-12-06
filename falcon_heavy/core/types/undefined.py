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

__all__ = (
    'UndefinedType',
    'Undefined',
)


class UndefinedType:

    _instance = None

    def __str__(self) -> str:
        return 'Undefined'

    def __repr__(self) -> str:
        return 'Undefined'

    def __eq__(self, other: ty.Any) -> bool:
        return self is other

    def __ne__(self, other: ty.Any) -> bool:
        return self is not other

    def __bool__(self) -> bool:
        return False

    __nonzero__ = __bool__

    def __lt__(self, other: ty.Any) -> None:
        self._cmp_err(other, '<')

    def __gt__(self, other: ty.Any) -> None:
        self._cmp_err(other, '>')

    def __le__(self, other: ty.Any) -> None:
        self._cmp_err(other, '<=')

    def __ge__(self, other: ty.Any) -> None:
        self._cmp_err(other, '>=')

    def _cmp_err(self, other: ty.Any, op: str) -> None:
        raise TypeError("unorderable types: {0}() {1} {2}()".format(
                        self.__class__.__name__, op, other.__class__.__name__))

    def __new__(cls: ty.Type['UndefinedType'], *args: ty.Any, **kwargs: ty.Any) -> 'UndefinedType':
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        elif cls is not UndefinedType:
            raise TypeError("type 'UndefinedType' is not an acceptable base type")
        return cls._instance

    def __init__(self) -> None:
        pass

    def __setattr__(self, name: str, value: ty.Any) -> None:
        raise TypeError("'UndefinedType' object does not support attribute assignment")


Undefined = UndefinedType()
