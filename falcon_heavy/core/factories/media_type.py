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

import mimeparse

from falcon_heavy.core import types as t, openapi as o
from falcon_heavy.core.utils import comma_delimited
from falcon_heavy.http.datastructures import FormStorage, FileStorage

from .media_handlers import get_media_handler
from .parameters import ParametersType, ParameterType, MediaParameterStyle
from .type import TypeFactory
from .headers import HeadersFactory
from .parameter_styles import BaseParameterStyle, PARAMETER_STYLES, IDENTITY_PARAMETER_STYLE

__all__ = (
    'Part',
    'AnyStorage',
    'AbstractMediaTypeFactory',
    'RequestMediaTypeFactory',
    'ResponseMediaTypeFactory',
)


class AllowedContentTypeValidator(t.AbstractValidator[str]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'unallowed': "Not allowed content type '{0}'. "
                     "Only the following content types are allowed: {1}"
    }

    def __init__(self, allowed: ty.Optional[ty.Iterable[str]] = None, **kwargs: ty.Any) -> None:
        super(AllowedContentTypeValidator, self).__init__(**kwargs)
        self.allowed = allowed

    def __call__(self, value: str, *args: ty.Any, **context: ty.Any) -> t.ValidationResult:
        if not self.allowed:
            return None

        if value in self.allowed:
            return None

        if mimeparse.best_match(self.allowed, value):
            return None

        return self.messages['unallowed'].format(
            value, comma_delimited(self.allowed))


AnyStorage = ty.Union[FormStorage, FileStorage]


class Part(ty.NamedTuple):
    custom_headers: ty.Mapping[str, ty.Any]
    content: ty.Any
    storage: AnyStorage


class PartAdapter(t.BaseType[Part]):

    MESSAGES: ty.ClassVar[t.Messages] = {
        'type': "Must be an instance of `FormStorage` or `FileStorage` classes",
        'deserialize': "Couldn't deserialize"
    }

    TYPES: ty.ClassVar[t.Types] = (FormStorage, FileStorage)

    def __init__(
            self,
            subtype: t.AbstractConvertible,
            default_content_type: ty.Optional[str] = None,
            **kwargs: ty.Any
    ) -> None:
        super(PartAdapter, self).__init__(**kwargs)
        self.subtype = subtype
        self.default_content_type = default_content_type

    def _cast(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        if isinstance(value, (list, tuple)) and len(value) == 1:
            return value[0]

        return value

    def _convert(
            self,
            value: AnyStorage,
            path: t.Path,
            *args: ty.Any,
            strict: bool = False,
            **context: ty.Any
    ) -> Part:
        content_type = value.content_type or self.default_content_type

        adapted: ty.Dict[str, ty.Any] = {
            'headers': value.headers
        }

        if content_type is not None:
            adapted['contentType'] = content_type

        strict = False
        if isinstance(value, FileStorage):
            adapted['content'] = value.stream

        else:
            adapted['content'] = value.value

            if content_type is not None:
                handler = get_media_handler(content_type)
                if handler is not None:
                    strict = True
                    try:
                        adapted['content'] = handler.deserialize(value.value)
                    except (ValueError, TypeError):
                        raise t.SchemaError(t.Error(path, self.messages['deserialize']))

        result = self.subtype.convert(adapted, path, strict=strict, **context)
        assert result is not None

        return Part(
            custom_headers=result['headers'],
            content=result['content'],
            storage=value
        )


class AbstractRequestMediaTypeFactory:

    def __init__(self, type_factory: TypeFactory) -> None:
        self.type_factory = type_factory

    def _generate(
            self,
            schema: o.SchemaObject,
            encoding: ty.Optional[ty.Mapping[str, o.EncodingObject]] = None
    ) -> t.AbstractConvertible:
        raise NotImplementedError()

    def generate(
            self,
            schema: o.SchemaObject,
            encoding: ty.Optional[ty.Mapping[str, o.EncodingObject]] = None
    ) -> t.AbstractConvertible:
        if schema.type == o.SCHEMA_TYPE.OBJECT and not schema.subschemas:
            return self._generate(schema, encoding=encoding)

        return self.type_factory.generate(schema)


class MultiPartMediaTypeFactory(AbstractRequestMediaTypeFactory):

    def __init__(self, type_factory: TypeFactory, headers_factory: HeadersFactory) -> None:
        super(MultiPartMediaTypeFactory, self).__init__(type_factory)
        self.headers_factory = headers_factory

    def _generate_part(
            self, schema: o.SchemaObject, property_encoding: ty.Optional[o.EncodingObject] = None) -> PartAdapter:
        properties: ty.MutableMapping[str, t.AbstractConvertible] = {}
        allowed_content_types: ty.Optional[ty.Iterable[str]] = None
        headers = None
        if property_encoding is not None:
            allowed_content_types = property_encoding.content_type
            headers = property_encoding.headers

        default_content_type = schema.default_content_type
        if not allowed_content_types and default_content_type is not None:
            allowed_content_types = (default_content_type, )

        properties['contentType'] = t.StringType(
            pattern=o.CONTENT_TYPE_PATTERN,
            validators=(AllowedContentTypeValidator(allowed_content_types), ),
            messages={'pattern': "Invalid content type"}
        )

        properties['headers'] = self.headers_factory.generate(headers or {})
        properties['content'] = self.type_factory.generate(schema)

        return PartAdapter(
            t.ObjectType(
                properties=properties,
                required={'headers', 'content'}
            ),
            default_content_type=default_content_type
        )

    def _generate_array_property(
            self, schema: o.SchemaObject, property_encoding: ty.Optional[o.EncodingObject] = None) -> t.ArrayType:
        assert schema.items_ is not None
        return t.ArrayType(
            item_type=self._generate_part(schema.items_, property_encoding=property_encoding),
            nullable=schema.nullable,
            default=schema.default,
            unique_items=schema.unique_items,
            min_items=schema.min_items,
            max_items=schema.max_items,
            enum=schema.enum
        )

    def _generate_property(
            self,
            schema: o.SchemaObject,
            property_encoding: ty.Optional[o.EncodingObject] = None
    ) -> t.AbstractConvertible:
        if schema.type == o.SCHEMA_TYPE.ARRAY:
            return self._generate_array_property(schema, property_encoding=property_encoding)
        else:
            return self._generate_part(schema, property_encoding=property_encoding)

    def _generate(
            self,
            schema: o.SchemaObject,
            encoding: ty.Optional[ty.Mapping[str, o.EncodingObject]] = None
    ) -> t.ObjectType:
        properties = {}
        read_only = set()
        write_only = set()
        if schema.properties_:
            for property_name, property_schema in schema.properties_.items():
                if property_schema.read_only:
                    read_only.add(property_name)
                    continue

                if property_schema.write_only:
                    write_only.add(property_name)

                property_encoding = None
                if encoding is not None:
                    property_encoding = encoding.get(property_name)

                properties[property_name] = self._generate_property(
                    property_schema, property_encoding=property_encoding)

        return t.ObjectType(
            properties=properties,
            required=schema.required,
            additional_properties=False,
            read_only=read_only,
            write_only=write_only,
            enum=schema.enum,
            messages={
                'additional_properties':
                    "Additional properties are not supported for multi-part media."
                    " The following additional properties were found: {0}"
            }
        )


class UrlencodedMediaTypeFactory(AbstractRequestMediaTypeFactory):

    def _generate(
            self,
            schema: o.SchemaObject,
            encoding: ty.Optional[ty.Mapping[str, o.EncodingObject]] = None
    ) -> ParametersType:
        if not schema.properties_:
            return ParametersType([])

        parameters = []
        for property_name, property_schema in schema.properties_.items():
            if property_schema.read_only:
                continue

            style: BaseParameterStyle = IDENTITY_PARAMETER_STYLE

            if property_schema.inferred_parameter_type is not None:
                property_encoding: ty.Optional[o.EncodingObject] = None
                if encoding is not None:
                    property_encoding = encoding.get(property_name)

                content_type: ty.Optional[str] = None
                if property_encoding is not None:
                    content_types = property_encoding.content_type
                    if content_types:
                        content_type = content_types[0]

                if content_type is not None:
                    handler = get_media_handler(content_type)
                    if handler is not None:
                        style = MediaParameterStyle(handler)
                else:
                    parameter_style: str = o.PARAMETER_STYLE.FORM
                    parameter_explode: bool = True
                    parameter_type: ty.Optional[str] = None
                    if property_encoding is not None:
                        parameter_style = property_encoding.style
                        parameter_explode = property_encoding.explode
                        parameter_type = property_encoding.x_parameter_type

                    if parameter_type is None:
                        parameter_type = property_schema.inferred_parameter_type

                    if parameter_type is not None:
                        style = PARAMETER_STYLES[
                            o.PARAMETER_LOCATION.QUERY,
                            parameter_type,
                            parameter_style,
                            parameter_explode
                        ]

            subtype = self.type_factory.generate(property_schema)

            parameters.append(ParameterType(
                subtype=subtype,
                name=property_name,
                style=style,
                required=schema.is_required(property_name),
                allow_empty_value=False
            ))

        return ParametersType(parameters, case_sensitive=True)


class AbstractMediaTypeFactory:

    def generate(self, content_type: str, media_type: o.MediaTypeObject) -> t.AbstractConvertible:
        raise NotImplementedError()


class RequestMediaTypeFactory(AbstractMediaTypeFactory):

    def __init__(self, type_factory: TypeFactory, headers_factory: HeadersFactory) -> None:
        self.type_factory = type_factory
        self.urlencoded_media_type_factory = UrlencodedMediaTypeFactory(type_factory)
        self.multipart_media_type_factory = MultiPartMediaTypeFactory(type_factory, headers_factory)

    def generate(self, content_type: str, media_type: o.MediaTypeObject) -> t.AbstractConvertible:
        if media_type.schema is None:
            return t.AnyType()

        if 'multipart/form-data' in content_type:
            return self.multipart_media_type_factory.generate(
                media_type.schema,
                encoding=media_type.encoding
            )

        elif any(ct in content_type for ct in (
            'application/x-www-form-urlencoded',
            'application/x-url-encoded',
        )):
            return self.urlencoded_media_type_factory.generate(
                media_type.schema,
                encoding=media_type.encoding
            )

        else:
            return self.type_factory.generate(media_type.schema)


class ResponseMediaTypeFactory(AbstractMediaTypeFactory):

    def __init__(self, type_factory: TypeFactory) -> None:
        self.type_factory = type_factory

    def generate(self, content_type: str, media_type: o.MediaTypeObject) -> t.AbstractConvertible:
        if media_type.schema is None:
            return t.AnyType()

        return self.type_factory.generate(media_type.schema)
