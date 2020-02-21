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

from .errors import Error

__all__ = (
    'SchemaError',
    'UndefinedResultError',
)


class SchemaError(Exception):

    def __init__(self, *errors: Error) -> None:
        self.errors = errors

    def __str__(self) -> str:
        return "\n".join(map(str, self.errors))

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, ', '.join(map(repr, self.errors)))


class UndefinedResultError(Exception):
    pass
