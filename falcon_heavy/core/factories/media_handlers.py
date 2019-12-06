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

import mimeparse

from falcon_heavy.core.encoders import FalconHeavyJSONEncoder

__all__ = (
    'AbstractMediaHandler',
    'JSONHandler',
    'register_media_handler',
    'get_media_handler',
)


class AbstractMediaHandler:

    __slots__ = ()

    def deserialize(self, value: str) -> ty.Any:
        raise NotImplementedError()

    def serialize(self, value: ty.Any) -> str:
        raise NotImplementedError()


class JSONHandler(AbstractMediaHandler):

    __slots__ = ()

    def deserialize(self, value: str) -> ty.Any:
        return json.loads(value)

    def serialize(self, value: ty.Mapping) -> str:
        return json.dumps(value, cls=FalconHeavyJSONEncoder, ensure_ascii=False)


_handlers: ty.Dict[str, AbstractMediaHandler] = {
    'application/json': JSONHandler(),
}


def register_media_handler(media_type: str, handler: AbstractMediaHandler) -> None:
    _handlers[media_type] = handler


def get_media_handler(
        media_type: str, default: ty.Optional[AbstractMediaHandler] = None) -> ty.Optional[AbstractMediaHandler]:
    try:
        return _handlers[media_type]
    except KeyError:
        pass

    best = mimeparse.best_match(_handlers.keys(), media_type)
    if best:
        return _handlers[best]

    return default
