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
from collections import defaultdict, Mapping

from falcon_heavy.core import types as t, openapi as o

from .utils import listtodict

__all__ = (
    'BaseParameterStyle',
    'IDENTITY_PARAMETER_STYLE',
    'PARAMETER_STYLES',
)


class BaseParameterStyle:

    __slots__ = ('explode', )

    def __init__(self, explode: bool = False):
        self.explode = explode

    def extract(self, params: ty.Mapping[str, ty.Any], name: str) -> ty.Any:
        return params.get(name, t.Undefined)

    def deserialize(self, value: ty.Any) -> ty.Any:
        return value

    def serialize(self, value: ty.Any) -> str:
        raise ValueError("Cannot apply this style when serializing")


class PathPrimitiveParameterSimpleStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value


class PathPrimitiveParameterLabelStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value[1:]


class PathPrimitiveParameterMatrixStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value.split('=', 1)[1]


class PathArrayParameterSimpleStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.List[str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value.split(',')


class PathArrayParameterLabelStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.List[str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        if not self.explode:
            return value[1:].split(',')
        else:
            return value[1:].split('.')


class PathArrayParameterMatrixStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.List[str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        if not self.explode:
            return value.split('=', 1)[1].split(',')
        else:
            return list(map(lambda x: x.split('=', 1)[1], value[1:].split(';')))


class PathObjectParameterSimpleStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Mapping[str, str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        if not self.explode:
            return listtodict(value.split(','))
        else:
            return listtodict(value.replace('=', ',').split(','))


class PathObjectParameterLabelStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Mapping[str, str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        if not self.explode:
            return listtodict(value[1:].split(','))
        else:
            return listtodict(value[1:].replace('=', '.').split('.'))


class PathObjectParameterMatrixStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Mapping[str, str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        if not self.explode:
            return listtodict(value.split('=', 1)[1].split(','))
        else:
            return listtodict(value[1:].replace('=', ';').split(';'))


class QueryPrimitiveParameterFormStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value


class QueryArrayParameterFormStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Collection:
        if self.explode:
            if isinstance(value, (list, tuple)):
                return value
            else:
                return [value]
        elif isinstance(value, str):
            return value.split(',')
        else:
            raise TypeError("Expected string")


class QueryArrayParameterSpaceDelimitedStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Collection:
        if self.explode:
            if isinstance(value, (list, tuple)):
                return value
            else:
                return [value]
        elif isinstance(value, str):
            return value.split(' ')
        else:
            raise TypeError("Expected string")


class QueryArrayParameterPipeDelimitedStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Collection:
        if self.explode:
            if isinstance(value, (list, tuple)):
                return value
            else:
                return [value]
        elif isinstance(value, str):
            return value.split('|')
        else:
            raise TypeError("Expected string")


class QueryObjectParameterFormStyle(BaseParameterStyle):

    __slots__ = ()

    def extract(self, params: ty.Mapping[str, ty.Any], name: str) -> ty.Any:
        if self.explode:
            return params
        else:
            return params.get(name, t.Undefined)

    def deserialize(self, value: ty.Any) -> ty.Mapping:
        if self.explode:
            if isinstance(value, Mapping):
                return value
            else:
                raise TypeError("Expected mapping")
        elif isinstance(value, str):
            return listtodict(value.split(','))
        else:
            raise TypeError("Expected string")


class QueryObjectParameterDeepObjectStyle(BaseParameterStyle):

    __slots__ = ()

    BRACKETS_PATTERN = re.compile(r'\[[^[\]]*]')

    def extract(self, params: ty.Mapping[str, ty.Any], name: str) -> ty.Any:
        params = {k: v for k, v in params.items() if k.startswith('{}['.format(name))}
        if not params:
            return t.Undefined

        result: ty.Dict[str, ty.Any] = {}
        for k, v in params.items():
            if re.sub(self.BRACKETS_PATTERN, '', k) != name:
                raise ValueError("Invalid brackets composition")

            segments = [segment[1:-1] for segment in re.findall(self.BRACKETS_PATTERN, k)]
            it = result
            for segment in segments[:-1]:
                if segment in it:
                    it = it[segment]
                else:
                    it[segment] = it = {}

                if not isinstance(it, dict):
                    raise ValueError("Invalid nested path")

            it[segments[-1]] = v

        return result

    def deserialize(self, value: ty.Any) -> ty.Mapping:
        if not isinstance(value, Mapping):
            raise TypeError("Expected mapping")

        return value


class HeaderPrimitiveParameterSimpleStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value

    def serialize(self, value: ty.Any) -> str:
        return str(value)


class HeaderArrayParameterSimpleStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.List[str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value.split(',')

    def serialize(self, value: ty.Any) -> str:
        if not isinstance(value, (list, tuple)):
            raise TypeError("Expected list or tuple")

        return ','.join(map(str, value))


class HeaderObjectParameterSimpleStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Mapping[str, str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        if not self.explode:
            return listtodict(value.split(','))
        else:
            return listtodict(value.replace('=', ',').split(','))

    def serialize(self, value: ty.Any) -> str:
        if not isinstance(value, Mapping):
            raise TypeError("Expected mapping")

        if not self.explode:
            return ','.join('%s,%s' % (k, v) for k, v in value.items())
        else:
            return ','.join('%s=%s' % (k, v) for k, v in value.items())


class CookiePrimitiveParameterFormStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value


class CookieArrayParameterFormStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.List[str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return value.split(',')


class CookieObjectParameterFormStyle(BaseParameterStyle):

    __slots__ = ()

    def deserialize(self, value: ty.Any) -> ty.Mapping[str, str]:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return listtodict(value.split(','))


class IdentityParameterStyle(BaseParameterStyle):

    __slots__ = ()


PARAMETER_STYLE_CLASSES: ty.Mapping[ty.Tuple[str, str, str], ty.Type[BaseParameterStyle]] = {
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.PRIMITIVE, o.PARAMETER_STYLE.SIMPLE):
        PathPrimitiveParameterSimpleStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.PRIMITIVE, o.PARAMETER_STYLE.LABEL):
        PathPrimitiveParameterLabelStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.PRIMITIVE, o.PARAMETER_STYLE.MATRIX):
        PathPrimitiveParameterMatrixStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.SIMPLE):
        PathArrayParameterSimpleStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.LABEL):
        PathArrayParameterLabelStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.MATRIX):
        PathArrayParameterMatrixStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.SIMPLE):
        PathObjectParameterSimpleStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.LABEL):
        PathObjectParameterLabelStyle,
    (o.PARAMETER_LOCATION.PATH, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.MATRIX):
        PathObjectParameterMatrixStyle,
    (o.PARAMETER_LOCATION.QUERY, o.PARAMETER_TYPE.PRIMITIVE, o.PARAMETER_STYLE.FORM):
        QueryPrimitiveParameterFormStyle,
    (o.PARAMETER_LOCATION.QUERY, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.FORM):
        QueryArrayParameterFormStyle,
    (o.PARAMETER_LOCATION.QUERY, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.SPACE_DELIMITED):
        QueryArrayParameterSpaceDelimitedStyle,
    (o.PARAMETER_LOCATION.QUERY, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.PIPE_DELIMITED):
        QueryArrayParameterPipeDelimitedStyle,
    (o.PARAMETER_LOCATION.QUERY, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.FORM):
        QueryObjectParameterFormStyle,
    (o.PARAMETER_LOCATION.QUERY, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.DEEP_OBJECT):
        QueryObjectParameterDeepObjectStyle,
    (o.PARAMETER_LOCATION.HEADER, o.PARAMETER_TYPE.PRIMITIVE, o.PARAMETER_STYLE.SIMPLE):
        HeaderPrimitiveParameterSimpleStyle,
    (o.PARAMETER_LOCATION.HEADER, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.SIMPLE):
        HeaderArrayParameterSimpleStyle,
    (o.PARAMETER_LOCATION.HEADER, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.SIMPLE):
        HeaderObjectParameterSimpleStyle,
    (o.PARAMETER_LOCATION.COOKIE, o.PARAMETER_TYPE.PRIMITIVE, o.PARAMETER_STYLE.FORM):
        CookiePrimitiveParameterFormStyle,
    (o.PARAMETER_LOCATION.COOKIE, o.PARAMETER_TYPE.ARRAY, o.PARAMETER_STYLE.FORM):
        CookieArrayParameterFormStyle,
    (o.PARAMETER_LOCATION.COOKIE, o.PARAMETER_TYPE.OBJECT, o.PARAMETER_STYLE.FORM):
        CookieObjectParameterFormStyle
}


PARAMETER_STYLES_NOT_EXPLODED: ty.Mapping[ty.Tuple[str, str, str, bool], BaseParameterStyle] = {
    (l, t, s, False): klass(False)
    for (l, t, s), klass in PARAMETER_STYLE_CLASSES.items()
}
PARAMETER_STYLES_EXPLODED: ty.Mapping[ty.Tuple[str, str, str, bool], BaseParameterStyle] = {
    (l, t, s, True): klass(True)
    for (l, t, s), klass in PARAMETER_STYLE_CLASSES.items()
}

IDENTITY_PARAMETER_STYLE = IdentityParameterStyle()

PARAMETER_STYLES: ty.DefaultDict[ty.Tuple[str, str, str, bool], BaseParameterStyle] = defaultdict(
    lambda: IDENTITY_PARAMETER_STYLE)
PARAMETER_STYLES.update(PARAMETER_STYLES_NOT_EXPLODED)
PARAMETER_STYLES.update(PARAMETER_STYLES_EXPLODED)
