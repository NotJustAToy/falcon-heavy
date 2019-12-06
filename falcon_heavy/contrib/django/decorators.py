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

import io
import typing as ty

from django.http import HttpRequest, HttpResponse, StreamingHttpResponse

from falcon_heavy.core import types as t
from falcon_heavy.contrib.decorators import AbstractOpenAPIDecorator, NormalizedRequest, ViewArgs, ViewKwargs
from falcon_heavy.contrib.responses import Cookie, ContentKind

__all__ = (
    'DjangoAbstractOpenAPIDecorator',
)


class DjangoAbstractOpenAPIDecorator(AbstractOpenAPIDecorator):

    def _get_normalized_request(
            self,
            instance: ty.Any,
            args: ViewArgs,
            kwargs: ViewKwargs
    ) -> NormalizedRequest:
        request: HttpRequest = args[0]

        headers = {}
        for name, value in request.META.items():
            if name == 'CONTENT_TYPE':
                headers['content-type'] = value

            elif name == 'CONTENT_LENGTH':
                headers['content-length'] = value

            elif name.startswith('HTTP_'):
                headers[name[5:].lower().replace('_', '-')] = value

        if not hasattr(request, '_body'):
            stream = request

        else:
            stream = io.BytesIO(request.body)

        return NormalizedRequest(
            original=request,
            method=request.method.lower(),
            path=request.path,
            path_params=kwargs,
            query_params=request.GET,
            headers=headers,
            cookies=request.COOKIES,
            stream=stream,
            content_length=int(request.META.get('CONTENT_LENGTH') or 0),
            content_type=request.META.get('CONTENT_TYPE', '')
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
    ) -> HttpResponse:
        if content_kind == ContentKind.STREAMING:
            response = StreamingHttpResponse(streaming_content=content, content_type=content_type, status=status_code)

        elif content_kind == ContentKind.MEDIA:
            response = HttpResponse(content=content, content_type=content_type, status=status_code)

        else:
            response = HttpResponse(content_type=content_type, status=status_code)

        for name, value in headers.items():
            response[name] = value

        if content_length is not None:
            response['content-length'] = str(content_length)

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
