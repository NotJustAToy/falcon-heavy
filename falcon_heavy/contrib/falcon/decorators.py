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

import typing as ty

import falcon
from falcon import status_codes, errors

from falcon_heavy.core import types as t
from falcon_heavy.contrib.decorators import AbstractOpenAPIDecorator, NormalizedRequest, ViewArgs, ViewKwargs
from falcon_heavy.contrib.responses import Cookie, ContentKind

__all__ = (
    'FalconAbstractOpenAPIDecorator',
)


class FalconAbstractOpenAPIDecorator(AbstractOpenAPIDecorator):

    def _get_normalized_request(
            self,
            instance: ty.Any,
            args: ViewArgs,
            kwargs: ViewKwargs
    ) -> NormalizedRequest:
        request: falcon.request.Request = args[0]

        return NormalizedRequest(
            original=request,
            method=request.method.lower(),
            path=request.path,
            path_params=kwargs,
            query_params=request.params,
            headers=request.headers,
            cookies=request.cookies,
            stream=request.bounded_stream,
            content_length=request.content_length or 0,
            content_type=request.content_type
        )

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
    ) -> None:
        response: falcon.Response = args[1]

        if content_type is not None:
            response.content_type = content_type

        if content_length is not None:
            response.content_length = content_length

        if content_kind == ContentKind.MEDIA:
            response.body = content

        elif content_kind == ContentKind.STREAMING:
            response.stream = content

        response.status = getattr(status_codes, 'HTTP_%s' % status_code)

        for name, value in headers.items():
            response.set_header(name, value)

        for cookie in cookies:
            response.set_cookie(
                cookie.name,
                cookie.value,
                expires=cookie.expires,
                max_age=cookie.max_age,
                domain=cookie.domain,
                path=cookie.path,
                secure=cookie.secure,
                http_only=cookie.http_only
            )

    def _handle_exception(self, request, instance, exception):
        if isinstance(exception, errors.HTTPError):
            raise exception
