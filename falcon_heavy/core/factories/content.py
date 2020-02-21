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

from falcon_heavy.core import openapi as o

from .common import SingleEntryMapType, ContentTypeBestMatchedType
from .media_type import AbstractMediaTypeFactory

__all__ = (
    'ContentFactory',
)


class ContentFactory:

    def __init__(self, media_type_factory: AbstractMediaTypeFactory) -> None:
        self.media_type_factory = media_type_factory

    def generate(self, content: ty.Mapping[str, o.MediaTypeObject]) -> ContentTypeBestMatchedType:
        return ContentTypeBestMatchedType(SingleEntryMapType(), {
            content_type: self.media_type_factory.generate(content_type, media_type)
            for content_type, media_type in content.items()
        })
