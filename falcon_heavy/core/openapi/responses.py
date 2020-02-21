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

from .base import BaseOpenAPIObjectType
from .response import ResponseObject, ResponseObjectType

__all__ = (
    'ResponsesObject',
    'ResponsesObjectType',
)


class ResponsesObject(t.Object):
    pass


class ResponsesObjectType(BaseOpenAPIObjectType[ResponsesObject], result_class=ResponsesObject):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'additional_properties':
            "Should contains HTTP status codes or `default`."
            " The following invalid definitions were found: {0}",
        'has_not_response_codes': "Responses must contains at least one response code"
    }

    PATTERN_PROPERTIES: ty.ClassVar[t.PatternProperties] = {
        re.compile(r'^[1-5](\d{2}|XX)$', re.IGNORECASE): t.ReferenceType[ResponseObject](ResponseObjectType())
    }

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'default': t.ReferenceType[ResponseObject](ResponseObjectType())
    }

    def validate_response_codes(self, value: ResponsesObject, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if all(k.startswith('x-') for k in value.pattern_properties.keys()):
            return self.messages['has_not_response_codes']

        return None
