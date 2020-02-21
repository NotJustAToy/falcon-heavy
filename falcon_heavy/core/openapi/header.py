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

from falcon_heavy.core import types as t

from .parameter import BaseParameterObject, BaseParameterObjectType
from .constants import PARAMETER_STYLE

__all__ = (
    'HeaderObject',
    'HeaderObjectType',
)


class HeaderObject(BaseParameterObject):
    pass


class HeaderObjectType(BaseParameterObjectType[HeaderObject], result_class=HeaderObject):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'deprecated': "Header '{0}' is deprecated"
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'style': t.StringType(enum=(PARAMETER_STYLE.SIMPLE,), default=PARAMETER_STYLE.SIMPLE),
        'explode': t.BooleanType(default=False)
    }
