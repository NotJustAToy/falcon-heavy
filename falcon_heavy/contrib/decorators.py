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
import operator

from mypy_extensions import Arg

import wrapt

import mimeparse

from cachetools import cachedmethod, LRUCache

from falcon_heavy.core import types as t, openapi as o

from .parsers import AbstractParser, ParseError
from .renderers import AbstractRenderer, RenderError
from .request import OpenAPIRequest
from .responses import OpenAPIResponse, Cookie, ContentKind
from .operations import OpenAPIOperations, OpenAPIOperation, OperationFindingError

__all__ = (
    'NormalizedRequest',
    'ViewArgs',
    'ViewKwargs',
    'AuthorizationDenyReasons',
    'View',
    'AbstractOpenAPIDecorator',
)


class NormalizedRequest(ty.NamedTuple):
    original: ty.Any
    method: str
    path: str
    path_params: ty.Mapping[str, ty.Any]
    query_params: ty.Mapping[str, ty.Any]
    headers: ty.Mapping[str, ty.Any]
    cookies: ty.Mapping[str, ty.Any]
    content_length: int
    content_type: ty.Optional[str]
    stream: ty.IO


ViewArgs = ty.Tuple[ty.Any, ...]
ViewKwargs = ty.Mapping[str, ty.Any]
AuthorizationDenyReasons = ty.List[ty.Tuple[str, str]]
View = ty.Callable[[Arg(OpenAPIRequest)], OpenAPIResponse]


class AbstractOpenAPIDecorator:

    default_response: OpenAPIResponse = OpenAPIResponse()

    def __init__(
            self,
            operations: OpenAPIOperations,
            parsers: ty.Iterable[AbstractParser] = (),
            renderers: ty.Iterable[AbstractRenderer] = ()
    ) -> None:
        self.operations = operations
        self.parsers: ty.Mapping[str, AbstractParser] = {
            media_type: parser
            for parser in parsers
            for media_type in parser.media_types
        }
        self.renderers: ty.Mapping[str, AbstractRenderer] = {
            media_type: renderer
            for renderer in renderers
            for media_type in renderer.media_types
        }
        self._get_parser_cache = LRUCache(1024)
        self._get_renderer_cache = LRUCache(1024)

    def _handle_not_found(
            self,
            request: NormalizedRequest,
            instance: ty.Any,
            exception: OperationFindingError
    ) -> OpenAPIResponse:
        raise NotImplementedError()

    def _handle_invalid_request(
            self,
            request: NormalizedRequest,
            operation: OpenAPIOperation,
            instance: ty.Any,
            exception: t.SchemaError
    ) -> OpenAPIResponse:
        raise NotImplementedError()

    def _handle_parse_error(
            self,
            request: NormalizedRequest,
            operation: OpenAPIOperation,
            instance: ty.Any,
            exception: ParseError
    ) -> OpenAPIResponse:
        raise NotImplementedError()

    def _handle_render_error(
            self,
            request: NormalizedRequest,
            operation: OpenAPIOperation,
            instance: ty.Any,
            exception: RenderError
    ) -> None:
        raise NotImplementedError()

    def _handle_invalid_response(
            self,
            request: NormalizedRequest,
            operation: OpenAPIOperation,
            instance: ty.Any,
            exception: t.SchemaError
    ) -> None:
        raise NotImplementedError()

    def _handle_authorization_failed(
            self,
            request: NormalizedRequest,
            operation: OpenAPIOperation,
            instance: ty.Any,
            reasons: ty.Iterable[ty.Tuple[str, str]]
    ) -> OpenAPIResponse:
        raise NotImplementedError()

    def _handle_exception(
            self,
            request: NormalizedRequest,
            instance: ty.Any,
            exception: BaseException
    ) -> OpenAPIResponse:
        raise NotImplementedError()

    def _get_normalized_request(
            self,
            instance: ty.Any,
            args: ViewArgs,
            kwargs: ViewKwargs
    ) -> NormalizedRequest:
        raise NotImplementedError()

    def _render_response(
            self,
            status_code: int,
            headers: ty.Mapping[str, ty.Any],
            cookies: ty.Iterable[Cookie],
            instance: ty.Any,
            args: ViewArgs,
            kwargs: ViewKwargs,
            content_type: ty.Optional[str] = None,
            content_length: ty.Optional[int] = None,
            content: ty.Any = t.Undefined,
            content_kind: ContentKind = ContentKind.UNDEFINED,
            **context: ty.Any
    ) -> ty.Any:
        raise NotImplementedError()

    def _render_500_error(self, instance: ty.Any, args: ViewArgs, kwargs: ViewKwargs) -> ty.Any:
        return self._render_response(500, {}, (), instance, args, kwargs)

    def _apply_api_key_security(
            self,
            request: NormalizedRequest,
            instance: ty.Any,
            key: ty.Optional[str],
            scopes: ty.Iterable[str],
            context: ty.MutableMapping[str, ty.Any]
    ) -> ty.Optional[str]:
        raise NotImplementedError()

    def _apply_http_security(
            self,
            request: NormalizedRequest,
            instance: ty.Any,
            scheme: str,
            token: ty.Optional[str],
            scopes: ty.Iterable[str],
            context: ty.MutableMapping[str, ty.Any],
            bearer_format: ty.Optional[str] = None
    ) -> ty.Optional[str]:
        raise NotImplementedError()

    def _apply_oauth2_security(
            self,
            request: NormalizedRequest,
            instance: ty.Any,
            flows: o.OAuthFlowsObject,
            scopes: ty.Iterable[str],
            context: ty.MutableMapping[str, ty.Any]
    ) -> ty.Optional[str]:
        raise NotImplementedError()

    def _apply_open_id_connect_security(
            self,
            request: NormalizedRequest,
            instance: ty.Any,
            open_id_connect_url: str,
            scopes: ty.Iterable[str],
            context: ty.MutableMapping[str, ty.Any]
    ) -> ty.Optional[str]:
        raise NotImplementedError()

    def _apply_security(
            self,
            request: NormalizedRequest,
            operation: OpenAPIOperation,
            instance: ty.Any,
            context: ty.MutableMapping[str, ty.Any]
    ) -> AuthorizationDenyReasons:
        reasons: AuthorizationDenyReasons = []
        for security in operation.security:
            for scheme_name, scopes in security.items():
                scheme = operation.security_schemes[scheme_name]
                reason = None
                if scheme.type == o.SECURITY_SCHEME_TYPE.API_KEY:
                    assert isinstance(scheme, o.APIKeySecuritySchemeObject)
                    name = scheme.name.lower()
                    location = scheme.location

                    key = None
                    if location == o.PARAMETER_LOCATION.HEADER:
                        key = request.headers.get(name)

                    elif location == o.PARAMETER_LOCATION.COOKIE:
                        key = request.cookies.get(name)

                    elif location == o.PARAMETER_LOCATION.QUERY:
                        key = request.query_params.get(name)

                    reason = self._apply_api_key_security(
                        request, instance, key, scopes, context)

                elif scheme.type == o.SECURITY_SCHEME_TYPE.HTTP:
                    assert isinstance(scheme, o.HttpSecuritySchemeObject)
                    reason = self._apply_http_security(
                        request,
                        instance,
                        scheme.scheme,
                        request.headers.get('authorization'),
                        scopes,
                        context,
                        bearer_format=scheme.bearer_format
                    )

                elif scheme.type == o.SECURITY_SCHEME_TYPE.OAUTH2:
                    assert isinstance(scheme, o.OAuth2SecuritySchemeObject)
                    reason = self._apply_oauth2_security(
                        request, instance, scheme.flows, scopes, context)

                elif scheme.type == o.SECURITY_SCHEME_TYPE.OPEN_ID_CONNECT:
                    assert isinstance(scheme, o.OpenIdConnectSecuritySchemeObject)
                    reason = self._apply_open_id_connect_security(
                        request, instance, scheme.open_id_connect_url, scopes, context)

                if reason is not None:
                    reasons.append((scheme_name, reason))
                    break

            else:
                break

        return reasons

    @cachedmethod(operator.attrgetter('_get_parser_cache'))
    def _get_parser(self, content_type: str) -> AbstractParser:
        if self.parsers:
            result = self.parsers.get(content_type)
            if result is not None:
                return result

            matched = mimeparse.best_match(self.parsers.keys(), content_type)
            if matched:
                return self.parsers[matched]

        raise ParseError("Couldn't find parser for '%s'" % content_type)

    def _parse(self, stream: ty.IO, content_type: str, content_length: int) -> ty.Any:
        parser = self._get_parser(content_type)
        return parser.parse(stream, content_type, content_length)

    @cachedmethod(operator.attrgetter('_get_renderer_cache'))
    def _get_renderer(self, content_type: str) -> AbstractRenderer:
        if self.renderers:
            renderer = self.renderers.get(content_type)
            if renderer is not None:
                return renderer

            matched = mimeparse.best_match(self.renderers.keys(), content_type)
            if matched:
                return self.renderers[matched]

        raise RenderError("Couldn't find renderer for '%s'" % content_type)

    def _render(self, content: ty.Any, content_type: str) -> str:
        renderer = self._get_renderer(content_type)
        return renderer.render(content)

    def _get_response(
            self,
            view: View,
            instance: ty.Any,
            request: NormalizedRequest,
            operation: OpenAPIOperation
    ) -> OpenAPIResponse:
        context: ty.Dict[str, ty.Any] = {}

        reasons = self._apply_security(request, operation, instance, context)

        if reasons:
            return self._handle_authorization_failed(
                request, operation, instance, reasons)

        content: ty.Any = t.Undefined

        if request.content_type and request.content_length > 0:
            try:
                content = self._parse(
                    request.stream,
                    request.content_type,
                    request.content_length
                )
            except ParseError as e:
                return self._handle_parse_error(request, operation, instance, e)

        elif request.content_length > 0:
            content = request.stream

        try:
            request_object = operation.request_converter.convert(
                request.path_params,
                request.query_params,
                request.headers,
                request.cookies,
                content=content,
                content_type=request.content_type
            )
        except t.SchemaError as e:
            return self._handle_invalid_request(
                request, operation, instance, e)

        assert request_object is not None

        try:
            response = view(OpenAPIRequest(
                original=request.original,
                content=request_object.content,
                path_params=request_object.path_params,
                query_params=request_object.query_params,
                header_params=request_object.header_params,
                cookie_params=request_object.cookie_params,
                context=context
            ))
        except Exception as e:
            result = self._handle_exception(request, instance, e)
            if result is None:
                raise
            return result

        return response or self.default_response

    @wrapt.decorator
    def __call__(self, view: View, instance: ty.Any, args: ViewArgs, kwargs: ViewKwargs) -> ty.Any:
        request = self._get_normalized_request(instance, args, kwargs)

        try:
            operation = self.operations.find(request.path, request.method)
        except OperationFindingError as e:
            return self._handle_not_found(request, instance, e)

        response = self._get_response(view, instance, request, operation)

        try:
            response_object = operation.response_converter.convert(
                response.status_code, response.headers, response.content, response.content_type)
        except t.SchemaError as e:
            try:
                self._handle_invalid_response(
                    request, operation, instance, e)
            except:  # noqa: E722
                pass

            return self._render_500_error(instance, args, kwargs)

        try:
            content: ty.Any = response_object.content
            if content is not t.Undefined and response.content_kind == ContentKind.MEDIA:
                assert response.content_type
                content = self._render(content, response.content_type)
        except RenderError as e:
            try:
                self._handle_render_error(
                    request, operation, instance, e)
            except:  # noqa: E722
                pass

            return self._render_500_error(instance, args, kwargs)

        return self._render_response(
            response.status_code,
            response_object.headers,
            response.cookies,
            instance,
            args,
            kwargs,
            content_type=response.content_type,
            content_length=response.content_length,
            content=content,
            content_kind=response.content_kind,
            **response.context
        )
