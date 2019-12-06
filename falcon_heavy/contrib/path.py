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

import re
import typing as ty

from falcon_heavy.utils import cached_property

__all__ = (
    'EXPRESSION_PATTERN',
    'OpenAPIPath',
)

# Template names should be able to start with A-Za-z
# but also contain 0-9_ in the remaining portion
EXPRESSION_PATTERN = r'{([a-zA-Z]\w*)}'


class OpenAPIPath:

    def __init__(self, template: str) -> None:
        if not template.startswith('/'):
            raise ValueError("Template must start with '/'")

        if '//' in template:
            raise ValueError("Template may not contain '//'")

        if template != '/' and template.endswith('/'):
            template = template[:-1]

        self._template = template

        # Get a list of field names
        self._fields = set(re.findall(EXPRESSION_PATTERN, template))

        # Convert Level 1 var patterns to equivalent named regex groups
        escaped = re.sub(r'[\.\(\)\[\]\?\*\+\^\|]', r'\\\g<0>', template)
        self._pattern = r'^' + re.sub(EXPRESSION_PATTERN, r'(?P<\1>[^/]+)', escaped) + r'$'

    @cached_property
    def regex(self) -> ty.Pattern:
        return re.compile(self._pattern)

    def match(self, path: str) -> ty.Optional[ty.Tuple[ty.Tuple, ty.Mapping]]:
        match = self.regex.match(path)
        if match:
            # If there are any named groups, use those as kwargs, ignoring
            # non-named groups. Otherwise, pass all non-named arguments as
            # positional arguments.
            kwargs = match.groupdict()
            args = () if kwargs else match.groups()
            return args, kwargs

        return None

    @property
    def template(self) -> str:
        return self._template

    @property
    def fields(self) -> ty.Set[str]:
        return self._fields

    @property
    def pattern(self) -> str:
        return self._pattern

    def __hash__(self):
        return hash(self._template)
