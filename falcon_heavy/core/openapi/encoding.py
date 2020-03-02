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

from .base import BaseOpenAPIObjectType
from .header import HeaderObject
from .constants import PARAMETER_STYLE, PARAMETER_TYPE
from .validators import CONTENT_TYPE_VALIDATOR

__all__ = (
    'EncodingObject',
    'EncodingObjectType',
)


class CommaDelimitedArrayType(t.ArrayType[str]):

    __slots__ = ()

    def _cast(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        if isinstance(value, str):
            return [content_type.strip() for content_type in value.split(',')]

        return super(CommaDelimitedArrayType, self)._cast(value, path, **context)


class EncodingObject(t.Object):

    @property
    def content_type(self) -> ty.Optional[ty.Sequence[str]]:
        return self.get('contentType')

    @property
    def headers(self) -> ty.Optional[ty.Mapping[str, HeaderObject]]:
        return self.get('headers')

    @property
    def style(self) -> str:
        return self['style']

    @property
    def explode(self) -> bool:
        return self.get('explode', self.style == PARAMETER_STYLE.FORM)

    @property
    def allow_reserved(self) -> bool:
        return self['allowReserved']

    @property
    def x_parameter_type(self) -> ty.Optional[str]:
        return self.get('x-parameterType')


class EncodingObjectType(BaseOpenAPIObjectType[EncodingObject], result_class=EncodingObject):

    __slots__ = ()

    PROPERTIES: ty.ClassVar[t.Properties] = {
        'contentType': CommaDelimitedArrayType(
            item_type=t.StringType(), max_items=2, validators=(CONTENT_TYPE_VALIDATOR,)),
        'headers': t.MapType[HeaderObject](
            t.ReferenceType[HeaderObject](t.LazyType[HeaderObject](lambda: HeaderObjectType()))),
        'style': t.StringType(
            enum=(
                PARAMETER_STYLE.FORM,
                PARAMETER_STYLE.SPACE_DELIMITED,
                PARAMETER_STYLE.PIPE_DELIMITED,
                PARAMETER_STYLE.DEEP_OBJECT
            ),
            default=PARAMETER_STYLE.FORM
        ),
        'explode': t.BooleanType(),
        'allowReserved': t.BooleanType(
            enum=[False],
            messages={'enum': "`allowReserved` permanently unsupported"},
            default=False
        ),
        'x-parameterType': t.StringType(enum=PARAMETER_TYPE),
    }


from .header import HeaderObjectType  # noqa
