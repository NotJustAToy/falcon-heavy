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

import os
import typing as ty
from urllib.parse import urljoin

import yaml

from falcon_heavy.core.types import RefHandlers, Path
from falcon_heavy.core import make_specification_conversion_context

from .openapi import OpenAPIObject, OpenAPIObjectType

__all__ = (
    'LoadFunc',
    'load_specification',
)


LoadFunc = ty.Callable[[ty.IO], ty.Mapping]


def load_specification(
        path: str,
        handlers: ty.Optional[RefHandlers] = None,
        load_func: LoadFunc = yaml.safe_load
) -> ty.Optional[OpenAPIObject]:
    with open(path) as fh:
        referrer = load_func(fh)
    base_uri = urljoin('file://', os.path.abspath(path))
    return OpenAPIObjectType().convert(
        referrer,
        Path(base_uri),
        **make_specification_conversion_context(base_uri, referrer, handlers=handlers)
    )
