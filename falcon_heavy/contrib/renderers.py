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

import json
import typing as ty

from falcon_heavy.core.encoders import FalconHeavyJSONEncoder

__all__ = (
    'RenderError',
    'AbstractRenderer',
    'JSONRenderer',
    'TextRenderer',
)


class RenderError(Exception):
    pass


class AbstractRenderer:

    media_types: ty.ClassVar[ty.Tuple[str, ...]] = NotImplemented

    def render(self, content: ty.Any) -> str:
        raise NotImplementedError()


class JSONRenderer(AbstractRenderer):

    media_types = ('application/json', )

    def render(self, content: ty.Any) -> str:
        try:
            return json.dumps(content, cls=FalconHeavyJSONEncoder, ensure_ascii=False)
        except (ValueError, TypeError) as e:
            raise RenderError("Couldn't render JSON") from e


class TextRenderer(AbstractRenderer):

    media_types = ('text/plain', )

    def render(self, content: ty.Any) -> str:
        try:
            return str(content)
        except (ValueError, TypeError) as e:
            raise RenderError("Couldn't render text") from e
