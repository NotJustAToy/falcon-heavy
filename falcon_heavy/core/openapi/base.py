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

from falcon_heavy.core import types as t

__all__ = (
    'BaseOpenAPIObjectType',
)

T = ty.TypeVar('T', bound=t.Object)


class BaseOpenAPIObjectType(t.ObjectType[T]):

    __slots__ = ()

    PATTERN_PROPERTIES: ty.ClassVar[t.PatternProperties] = {
        re.compile(r'^x-'): t.AnyType()
    }

    ADDITIONAL_PROPERTIES: ty.ClassVar[t.AdditionalProperties] = False
