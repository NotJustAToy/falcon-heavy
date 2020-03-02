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

import os
import enum
import datetime
import mimetypes
import typing as ty
from pathlib import Path
from urllib.parse import quote

from falcon_heavy.core import types as t

__all__ = (
    'Cookie',
    'ContentKind',
    'Headers',
    'Cookies',
    'OpenAPIResponse',
    'OpenAPITextResponse',
    'OpenAPIJSONResponse',
    'OpenAPIStreamingResponse',
    'OpenAPIFileResponse',
)

T = ty.TypeVar('T', bound='Cookie')


class Cookie:

    __slots__ = (
        'name',
        'value',
        'max_age',
        'expires',
        'path',
        'domain',
        'secure',
        'http_only',
        'same_site'
    )

    max_age: ty.Optional[int]

    def __init__(
            self,
            name: str,
            value: str = '',
            max_age: ty.Optional[ty.Union[int, datetime.timedelta]] = None,
            expires: ty.Optional[ty.Union[str, datetime.datetime]] = None,
            path: str = '/',
            domain: ty.Optional[str] = None,
            secure: bool = False,
            http_only: bool = False,
            same_site: ty.Optional[str] = None
    ) -> None:
        self.name = name
        self.value = value
        if isinstance(max_age, datetime.timedelta):
            max_age = (max_age.days * 60 * 60 * 24) + max_age.seconds
        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.secure = secure
        self.http_only = http_only
        if same_site is not None and same_site.lower() not in ('lax', 'strict'):
            raise ValueError("Same site must be 'lax' or 'strict'")
        self.same_site = same_site

    @classmethod
    def set(
            cls: ty.Type[T],
            name: str,
            value: str = '',
            max_age: ty.Optional[int] = None,
            expires: ty.Optional[datetime.datetime] = None,
            path: str = '/',
            domain: ty.Optional[str] = None,
            secure: bool = False,
            http_only: bool = False,
            same_site: ty.Optional[str] = None
    ) -> T:
        return cls(name, value=value, max_age=max_age, expires=expires, path=path,
                   domain=domain, secure=secure, http_only=http_only, same_site=same_site)

    @classmethod
    def delete(
            cls: ty.Type[T],
            name: str,
            path: str = '/',
            domain: ty.Optional[str] = None
    ) -> T:
        # Most browsers ignore the Set-Cookie header if the cookie name starts
        # with __Host- or __Secure- and the cookie doesn't use the secure flag.
        secure = name.startswith(('__Secure-', '__Host-'))
        return cls(name, max_age=0, path=path, domain=domain, secure=secure,
                   expires='Thu, 01 Jan 1970 00:00:00 GMT')


class ContentKind(enum.Enum):

    UNDEFINED = enum.auto()
    MEDIA = enum.auto()
    STREAMING = enum.auto()


Headers = ty.Mapping[str, ty.Any]
Cookies = ty.Iterable[Cookie]


class OpenAPIResponse:

    __slots__ = (
        'content',
        'content_kind',
        'status_code',
        'headers',
        'cookies',
        'context'
    )

    def __init__(
            self,
            media: ty.Any = t.Undefined,
            stream: ty.Optional[ty.IO] = None,
            status_code: int = 200,
            headers: ty.Optional[Headers] = None,
            cookies: ty.Optional[Cookies] = None,
            content_type: ty.Optional[str] = None,
            content_length: ty.Optional[int] = None,
            **context: ty.Any
    ) -> None:
        self.content: ty.Any = t.Undefined
        self.content_kind = ContentKind.UNDEFINED
        if media is not t.Undefined:
            self.media = media
        if stream is not None:
            self.stream = stream
        self.status_code = status_code
        self.headers: ty.Dict[str, ty.Any] = {}
        if headers is not None:
            self.headers.update(headers)
        self.cookies = cookies or ()
        if media is not t.Undefined and content_type is None:
            raise ValueError("You should specify content type")
        if content_type is not None:
            self.content_type = content_type
        if content_length is not None:
            self.content_length = content_length
        self.context = context

    @property
    def media(self) -> ty.Any:
        return self.content if self.content_kind == ContentKind.MEDIA else None

    @media.setter
    def media(self, value: ty.Any) -> None:
        self.content, self.content_kind = value, ContentKind.MEDIA

    @property
    def stream(self) -> ty.Optional[ty.IO]:
        return self.content if self.content_kind == ContentKind.STREAMING else None

    @stream.setter
    def stream(self, value: ty.IO) -> None:
        self.content, self.content_kind = value, ContentKind.STREAMING

    @property
    def content_type(self) -> ty.Optional[str]:
        return self.headers.get('content-type')

    @content_type.setter
    def content_type(self, value: str) -> None:
        self.headers['content-type'] = value

    @property
    def content_length(self) -> ty.Optional[int]:
        return self.headers.get('content-length')

    @content_length.setter
    def content_length(self, value: int) -> None:
        self.headers['content-length'] = value


class OpenAPITextResponse(OpenAPIResponse):

    def __init__(
            self,
            media: ty.Any,
            status_code: int = 200,
            headers: ty.Optional[Headers] = None,
            cookies: ty.Optional[Cookies] = None,
            content_type: str = 'text/plain',
            **context: ty.Any
    ) -> None:
        super(OpenAPITextResponse, self).__init__(
            media=media,
            status_code=status_code,
            headers=headers,
            cookies=cookies,
            content_type=content_type,
            **context
        )


class OpenAPIJSONResponse(OpenAPIResponse):

    def __init__(
            self,
            media: ty.Any,
            status_code: int = 200,
            headers: ty.Optional[Headers] = None,
            cookies: ty.Optional[Cookies] = None,
            content_type: str = 'application/json',
            **context: ty.Any
    ) -> None:
        super(OpenAPIJSONResponse, self).__init__(
            media=media,
            status_code=status_code,
            headers=headers,
            cookies=cookies,
            content_type=content_type,
            **context
        )


class OpenAPIStreamingResponse(OpenAPIResponse):

    def __init__(
            self,
            stream: ty.IO,
            status_code: int = 200,
            headers: ty.Optional[Headers] = None,
            cookies: ty.Optional[Cookies] = None,
            content_type: str = 'application/octet-stream',
            content_length: ty.Optional[int] = None,
            **context: ty.Any
    ) -> None:
        super(OpenAPIStreamingResponse, self).__init__(
            stream=stream,
            status_code=status_code,
            headers=headers,
            cookies=cookies,
            content_type=content_type,
            content_length=content_length,
            **context
        )


ENCODING_MAP = {
    'bzip2': 'application/x-bzip',
    'gzip': 'application/gzip',
    'xz': 'application/x-xz'
}


class OpenAPIFileResponse(OpenAPIResponse):

    def __init__(
            self,
            path: ty.Optional[ty.Union[str, Path]] = None,
            file: ty.Optional[ty.IO] = None,
            as_attachment: bool = False,
            filename: ty.Optional[str] = None,
            status_code: int = 200,
            headers: ty.Optional[Headers] = None,
            cookies: ty.Optional[Cookies] = None,
            content_type: ty.Optional[str] = None,
            **context: ty.Any
    ):
        content_length = None

        if path is not None:
            file = open(path, 'rb')
            filename = filename or os.path.basename(path)
            content_length = os.path.getsize(path)

        elif file is not None and hasattr(file, 'getbuffer'):
            content_length = file.getbuffer().nbytes  # type: ignore

        if content_type is None and filename is not None:
            content_type, encoding = mimetypes.guess_type(filename)
            if encoding is not None:
                content_type = ENCODING_MAP.get(encoding, content_type)

        super(OpenAPIFileResponse, self).__init__(
            stream=file,
            content_length=content_length,
            content_type=content_type or 'application/octet-stream',
            status_code=status_code,
            headers=headers,
            cookies=cookies,
            as_attachment=as_attachment,
            filename=filename,
            **context
        )

        if as_attachment and filename is not None:
            try:
                filename.encode('ascii')
                file_expr = 'filename="{}"'.format(filename)
            except UnicodeEncodeError:
                file_expr = "filename*=utf-8''{}".format(quote(filename))

            self.headers['content-disposition'] = 'attachment; {}'.format(file_expr)
