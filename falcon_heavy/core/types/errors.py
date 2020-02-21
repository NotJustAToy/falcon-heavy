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

from .path import Path

__all__ = (
    'Error',
)


class Error:

    __slots__ = (
        'path',
        'message'
    )

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message

    def __eq__(self, other: ty.Any) -> bool:
        if not isinstance(other, Error):
            raise NotImplementedError()

        return self.path == other.path and self.message == other.message

    def __hash__(self) -> int:
        return hash((self.path, self.message))

    def __str__(self) -> str:
        return "%s: %s" % (self.path, self.message)

    def __repr__(self) -> str:
        return "%s(%r, %r)" % (self.__class__.__name__, self.path, self.message)
