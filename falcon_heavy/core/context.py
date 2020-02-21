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

__all__ = (
    'make_specification_conversion_context',
    'make_request_conversion_context',
    'make_response_conversion_context',
)


def make_specification_conversion_context(
        base_uri: str, referrer: ty.Mapping, handlers: ty.Optional[t.RefHandlers] = None) -> ty.Mapping[str, ty.Any]:
    return {
        'registry': {},
        'operation_ids': {},
        'entity': t.ConvertibleEntity.SPECIFICATION,
        'ref_resolver': t.RefResolver(base_uri, referrer, handlers=handlers)
    }


def make_request_conversion_context() -> ty.Mapping[str, ty.Any]:
    return {
        'entity': t.ConvertibleEntity.REQUEST
    }


def make_response_conversion_context() -> ty.Mapping[str, ty.Any]:
    return {
        'entity': t.ConvertibleEntity.RESPONSE
    }
