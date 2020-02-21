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
from itertools import groupby
from collections import Mapping

from falcon_heavy.core import types as t, openapi as o

from .datastructures import CaseInsensitiveDict
from .registry import registered, hashkey
from .media_handlers import get_media_handler, AbstractMediaHandler
from .parameter_styles import BaseParameterStyle, PARAMETER_STYLES, IDENTITY_PARAMETER_STYLE
from .type import TypeFactory

__all__ = (
    'ParameterType',
    'ParametersType',
    'MediaParameterStyle',
    'ParameterFactory',
    'ParametersFactory',
)


class ParameterType(t.BaseType):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'extract': "Couldn't extract parameter '{0}'",
        'empty': "Value can't be empty",
        'required': "Missing required parameter",
        'deserialize': "Couldn't deserialize",
        'serialize': "Couldn't serialize"
    }

    TYPES: ty.ClassVar[t.Types] = (Mapping, )

    __slots__ = (
        'subtype',
        'name',
        'style',
        'required',
        'allow_empty_value',
        'strict'
    )

    def __init__(
            self,
            subtype: t.AbstractConvertible,
            name: str,
            style: BaseParameterStyle,
            required: bool = False,
            allow_empty_value: ty.Optional[bool] = None,
            strict: bool = False,
            **kwargs: ty.Any
    ) -> None:
        super(ParameterType, self).__init__(**kwargs)
        self.subtype = subtype
        self.name = name
        self.style = style
        self.required = required
        self.allow_empty_value = allow_empty_value
        self.strict = strict

    def _convert(
            self,
            value: ty.Mapping[str, str],
            path: t.Path,
            *args: ty.Any,
            strict: bool = True,
            entity: ty.Optional[t.ConvertibleEntity] = None,
            **context: ty.Any
    ) -> ty.Any:
        try:
            value = self.style.extract(value, self.name)
        except (ValueError, TypeError, LookupError):
            raise t.SchemaError(t.Error(path, self.messages['extract'].format(self.name)))

        if value is t.Undefined and self.required:
            raise t.SchemaError(t.Error(path, self.messages['required']))

        elif value is not t.Undefined:
            if not value and self.allow_empty_value is not None and not self.allow_empty_value:
                raise t.SchemaError(t.Error(path, self.messages['empty']))

            if entity == t.ConvertibleEntity.REQUEST:
                try:
                    value = self.style.deserialize(value)
                except (TypeError, ValueError):
                    raise t.SchemaError(t.Error(path, self.messages['deserialize']))

        if entity == t.ConvertibleEntity.REQUEST:
            strict = self.strict

        result = self.subtype.convert(
            value, path, strict=strict, entity=entity, **context)

        if entity == t.ConvertibleEntity.RESPONSE:
            try:
                return self.style.serialize(result)
            except (TypeError, ValueError):
                raise t.SchemaError(t.Error(path, self.messages['serialize']))

        return result


class ParametersType(t.BaseType[ty.Mapping]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'type': "Must be a mapping"
    }

    TYPES: ty.ClassVar[t.Types] = (Mapping, )

    __slots__ = ('parameters', 'case_sensitive')

    def __init__(self, parameters: ty.Iterable[ParameterType], case_sensitive: bool = False, **kwargs: ty.Any) -> None:
        super(ParametersType, self).__init__(**kwargs)
        self.parameters = parameters
        self.case_sensitive = case_sensitive

    def _convert(self, value: ty.Mapping, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Mapping:
        result = {}
        errors: ty.List[t.Error] = []

        if not self.case_sensitive:
            value = CaseInsensitiveDict(value)

        for parameter in self.parameters:
            try:
                result[parameter.name] = parameter.convert(value, path / parameter.name, **context)
            except t.SchemaError as e:
                errors.extend(e.errors)
                continue

            except t.UndefinedResultError:
                continue

        if errors:
            raise t.SchemaError(*errors)

        return result


class MediaParameterStyle(BaseParameterStyle):

    __slots__ = ('handler', )

    def __init__(self, handler: AbstractMediaHandler, **kwargs: ty.Any) -> None:
        super(MediaParameterStyle, self).__init__(**kwargs)
        self.handler = handler

    def deserialize(self, value: ty.Any) -> ty.Any:
        if not isinstance(value, str):
            raise TypeError("Expected string")

        return self.handler.deserialize(value)

    def serialize(self, value: ty.Any) -> str:
        return self.handler.serialize(value)


class ParameterFactory:

    def __init__(self, type_factory: TypeFactory) -> None:
        self.type_factory = type_factory

    @registered(key=lambda location, name, parameter: hashkey(location, name, parameter.path))
    def generate(
            self,
            location: str,
            name: str,
            parameter: ty.Union[o.AnyParameterObject, o.HeaderObject]
    ) -> ParameterType:
        strict = False
        style: BaseParameterStyle = IDENTITY_PARAMETER_STYLE

        if parameter.schema:
            parameter_type = parameter.schema.parameter_type

            if parameter_type is not None:
                style = PARAMETER_STYLES[
                    location, parameter_type, parameter.style, parameter.explode
                ]

            subtype = self.type_factory.generate(parameter.schema)

        elif parameter.content is not None:
            content_type, media_type = parameter.content
            if media_type.schema is None:
                subtype = t.AnyType()
            else:
                subtype = self.type_factory.generate(media_type.schema)

            handler = get_media_handler(content_type)
            if handler is not None:
                style = MediaParameterStyle(handler)
                strict = True

        else:
            subtype = t.AnyType()

        allow_empty_value = None
        if isinstance(parameter, o.QueryParameterObject):
            allow_empty_value = parameter.allow_empty_value

        return ParameterType(
            subtype=subtype,
            name=name,
            style=style,
            required=parameter.required,
            allow_empty_value=allow_empty_value,
            strict=strict
        )


class DummyType(t.AbstractConvertible):

    __slots__ = ()

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        return {}


DUMMY = DummyType()


class ParametersFactory:

    def __init__(self, parameter_factory: ParameterFactory) -> None:
        self.parameter_factory = parameter_factory

    def generate(self, parameters: ty.Optional[ty.Iterable[o.AnyParameterObject]] = None) -> t.ObjectType:
        properties: ty.Dict[str, t.AbstractConvertible] = {}

        if parameters:
            for location, parameters in groupby(parameters, key=lambda x: x.location):
                properties[location] = ParametersType(
                    parameters=[
                        self.parameter_factory.generate(location, parameter.name, parameter)
                        for parameter in parameters
                    ]
                )

        return t.ObjectType(
            properties=properties,
            additional_properties=DUMMY
        )
