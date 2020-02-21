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
from falcon_heavy.core.utils import comma_delimited

__all__ = (
    'CONTENT_TYPE_PATTERN',
    'CONTENT_TYPE_VALIDATOR',
)


CONTENT_TYPE_PATTERN = re.compile(r'^((\w+/(\*|\w+))|(\*/\*)).*$', re.IGNORECASE)


class ContentTypeValidator(t.AbstractValidator[ty.Collection[str]]):

    __slots__ = ()

    MESSAGES: ty.ClassVar[t.Messages] = {
        'invalid_content_types': "The following content types are invalid: {0}"
    }

    def __call__(self, value: ty.Collection[str], *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        invalid_content_types = []
        for content_type in value:
            if not CONTENT_TYPE_PATTERN.match(content_type):
                invalid_content_types.append(content_type)

        if invalid_content_types:
            return self.messages['invalid_content_types'].format(comma_delimited(invalid_content_types))

        return None


CONTENT_TYPE_VALIDATOR = ContentTypeValidator()
