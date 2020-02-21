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

import re
import typing as ty

from django.urls.resolvers import URLPattern

from falcon_heavy.utils import cached_property
from falcon_heavy.contrib.path import OpenAPIPath

__all__ = (
    'PathPattern',
    'route',
)


class PathPattern:

    def __init__(self, path: OpenAPIPath, name: ty.Optional[str] = None) -> None:
        self.path = path
        self.name = name
        self.converters: ty.Dict = {}

    def describe(self) -> str:
        """
        Format the URI template pattern for display in warning messages.
        """
        description = "'{}'".format(self)
        if self.name:
            description += " [name='{}']".format(self.name)
        return description

    def match(self, path: str) -> ty.Optional[ty.Tuple[ty.List, ty.Tuple, ty.Mapping[str, ty.Any]]]:
        if not path.startswith('/'):
            path = '/' + path
        match = self.path.match(path)
        if match:
            args, kwargs = match
            return [], args, kwargs

        return None

    @cached_property
    def regex(self) -> ty.Pattern:
        return re.compile(self.path.pattern[2:])  # remove '^/' for django reverse urls purpose

    @staticmethod
    def check() -> ty.List:
        return []

    def __str__(self) -> str:
        return self.path.template


def route(
        path: OpenAPIPath,
        view: ty.Callable,
        kwargs: ty.Optional[ty.Mapping[str, ty.Any]] = None,
        name: ty.Optional[str] = None
) -> URLPattern:
    return URLPattern(PathPattern(path), view, default_args=kwargs, name=name)
