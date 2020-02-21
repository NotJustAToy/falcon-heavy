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

__all__ = (
    'PARAMETER_LOCATION',
    'PARAMETER_STYLE',
    'SCHEMA_TYPE',
    'PRIMITIVE_SCHEMA_TYPES',
    'SCHEMA_FORMAT',
    'SECURITY_SCHEME_TYPE',
    'HTTP_SCHEME',
    'HTTP_METHOD',
    'HTTP_METHODS',
    'PARAMETER_TYPE',
)


class ParameterLocation(ty.NamedTuple):
    PATH: str = 'path'
    QUERY: str = 'query'
    HEADER: str = 'header'
    COOKIE: str = 'cookie'


PARAMETER_LOCATION = ParameterLocation()


class ParameterStyle(ty.NamedTuple):
    MATRIX: str = 'matrix'
    LABEL: str = 'label'
    FORM: str = 'form'
    SIMPLE: str = 'simple'
    SPACE_DELIMITED: str = 'spaceDelimited'
    PIPE_DELIMITED: str = 'pipeDelimited'
    DEEP_OBJECT: str = 'deepObject'


PARAMETER_STYLE = ParameterStyle()


class SchemaType(ty.NamedTuple):
    INTEGER: str = 'integer'
    NUMBER: str = 'number'
    STRING: str = 'string'
    BOOLEAN: str = 'boolean'
    ARRAY: str = 'array'
    OBJECT: str = 'object'


SCHEMA_TYPE = SchemaType()


PRIMITIVE_SCHEMA_TYPES: ty.FrozenSet[str] = frozenset((
    SCHEMA_TYPE.STRING,
    SCHEMA_TYPE.NUMBER,
    SCHEMA_TYPE.INTEGER,
    SCHEMA_TYPE.BOOLEAN
))


class SchemaFormat(ty.NamedTuple):
    INT32: str = 'int32'
    INT64: str = 'int64'
    FLOAT: str = 'float'
    DOUBLE: str = 'double'
    BYTE: str = 'byte'
    BINARY: str = 'binary'
    DATE: str = 'date'
    DATETIME: str = 'date-time'
    PASSWORD: str = 'password'


SCHEMA_FORMAT = SchemaFormat()


class SecuritySchemeType(ty.NamedTuple):
    API_KEY: str = 'apiKey'
    HTTP: str = 'http'
    OAUTH2: str = 'oauth2'
    OPEN_ID_CONNECT: str = 'openIdConnect'


SECURITY_SCHEME_TYPE = SecuritySchemeType()


class HttpScheme(ty.NamedTuple):
    HTTP: str = 'http'
    HTTPS: str = 'https'


HTTP_SCHEME = HttpScheme()


class HttpMethod(ty.NamedTuple):
    GET: str = 'get'
    PUT: str = 'put'
    POST: str = 'post'
    DELETE: str = 'delete'
    OPTIONS: str = 'options'
    HEAD: str = 'head'
    PATCH: str = 'patch'
    TRACE: str = 'trace'


HTTP_METHOD = HttpMethod()


HTTP_METHODS: ty.Tuple[str, ...] = (
    HTTP_METHOD.GET,
    HTTP_METHOD.PUT,
    HTTP_METHOD.POST,
    HTTP_METHOD.DELETE,
    HTTP_METHOD.OPTIONS,
    HTTP_METHOD.HEAD,
    HTTP_METHOD.PATCH,
    HTTP_METHOD.TRACE
)


class ParameterType(ty.NamedTuple):
    PRIMITIVE: str = 'primitive'
    ARRAY: str = 'array'
    OBJECT: str = 'object'


PARAMETER_TYPE = ParameterType()
