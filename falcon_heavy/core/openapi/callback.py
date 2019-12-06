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

from falcon_heavy.core import types as t

from .base import BaseOpenAPIObjectType

__all__ = (
    'CallbackObject',
    'CallbackObjectType',
)


class CallbackObject(t.Object):
    pass


class CallbackObjectType(BaseOpenAPIObjectType[CallbackObject], result_class=CallbackObject):

    __slots__ = ()

    ADDITIONAL_PROPERTIES: ty.ClassVar[
        t.AdditionalProperties] = t.LazyType['PathItemObject'](lambda: PathItemObjectType())


from .path_item import PathItemObject, PathItemObjectType  # noqa
