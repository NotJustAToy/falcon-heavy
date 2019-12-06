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

from werkzeug.datastructures import Headers

from flask import request, current_app

from falcon_heavy.core import types as t
from falcon_heavy.contrib.decorators import AbstractOpenAPIDecorator, NormalizedRequest, ViewArgs, ViewKwargs
from falcon_heavy.contrib.responses import Cookie, ContentKind

__all__ = (
    'FlaskAbstractOpenAPIDecorator',
)


def iter_chunks(f: ty.IO, chunk_size: int = 16 * 1024) -> ty.Generator[ty.AnyStr, None, None]:
    while True:
        buf = f.read(chunk_size)
        if buf:
            yield buf
        else:
            break


class FlaskAbstractOpenAPIDecorator(AbstractOpenAPIDecorator):

    def _get_normalized_request(
            self,
            instance: ty.Any,
            args: ViewArgs,
            kwargs: ViewKwargs
    ) -> NormalizedRequest:
        return NormalizedRequest(
            original=request,
            method=request.method.lower(),
            path=request.path,
            path_params=request.view_args,
            query_params=request.args,
            headers=request.headers,
            cookies=request.cookies,
            stream=ty.cast(ty.IO, request.stream),
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
    ) -> ty.Any:
        headers = Headers(headers)

        if content_length is not None:
            headers["content-length"] = content_length

        response_class = current_app.response_class

        if content_kind == ContentKind.STREAMING:
            response = response_class(
                response=iter_chunks(content),
                status=status_code,
                headers=headers,
                content_type=content_type
            )

        elif content_kind == ContentKind.MEDIA:
            response = response_class(
                response=content,
                status=status_code,
                headers=headers,
                content_type=content_type
            )

        else:
            response = response_class(
                status=status_code,
                headers=headers,
                content_type=content_type
            )

        for cookie in cookies:
            response.set_cookie(
                cookie.name,
                value=cookie.value,
                max_age=cookie.max_age,
                expires=cookie.expires,
                path=cookie.path,
                domain=cookie.domain,
                secure=cookie.secure,
                httponly=cookie.http_only,
                samesite=cookie.same_site
            )

        return response
