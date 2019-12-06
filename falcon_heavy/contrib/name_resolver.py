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

from .utils import import_string

__all__ = (
    'AbstractNameResolver',
    'RuntimeNameResolver',
)


class AbstractNameResolver:

    def resolve(self, path: str, silent: bool = True) -> None:
        raise NotImplementedError()


class RuntimeNameResolver(AbstractNameResolver):

    def __init__(self, base_path: ty.Optional[str] = None) -> None:
        self.base_path = base_path

    def resolve(self, path: str, silent: bool = True) -> ty.Any:
        if self.base_path:
            path = '%s.%s' % (self.base_path, path)

        try:
            resource = import_string(path)
        except ImportError:
            if silent:
                return None
            raise

        return resource
