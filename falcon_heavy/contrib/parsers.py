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

import json
import typing as ty

import mimeparse

from falcon_heavy.http.multipart_parser import MultiPartParser as _MultiPartParser, MultiPartParserError
from falcon_heavy.http.exceptions import RequestDataError
from falcon_heavy.http.datastructures import MultiValueDict
from falcon_heavy.http.utils import limited_parse_qsl

__all__ = (
    'ParseError',
    'AbstractParser',
    'JSONParser',
    'MultiPartParser',
    'FormParser',
)


class ParseError(Exception):
    pass


class AbstractParser:

    media_types: ty.ClassVar[ty.Tuple[str, ...]] = NotImplemented

    def parse(self, stream: ty.IO, content_type: str, content_length: int) -> ty.Any:
        raise NotImplementedError()


class JSONParser(AbstractParser):

    media_types = ('application/json', )

    def __init__(self, encoding: str = 'utf-8') -> None:
        self.encoding = encoding

    def parse(self, stream: ty.IO, content_type: str, content_length: int) -> ty.Mapping:
        params = mimeparse.parse_mime_type(content_type)[2]
        try:
            return json.loads(stream.read().decode(params.get('charset', self.encoding)))
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise ParseError("Couldn't parse JSON") from e


class MultiPartParser(AbstractParser):

    media_types = ('multipart/form-data', )

    def __init__(
            self,
            data_upload_max_number_fields: int = 1000,
            data_upload_max_memory_size: int = 2621440,
            file_upload_max_memory_size: int = 2621440,
            file_upload_temp_dir: ty.Optional[str] = None,
            encoding: str = 'utf-8'
    ) -> None:
        self.data_upload_max_number_fields = data_upload_max_number_fields
        self.data_upload_max_memory_size = data_upload_max_memory_size
        self.file_upload_max_memory_size = file_upload_max_memory_size
        self.file_upload_temp_dir = file_upload_temp_dir
        self.encoding = encoding

    def parse(self, stream: ty.IO, content_type: str, content_length: int) -> ty.Mapping[str, ty.List[ty.Any]]:
        parser = _MultiPartParser(
            stream,
            content_type,
            content_length,
            data_upload_max_number_fields=self.data_upload_max_number_fields,
            data_upload_max_memory_size=self.data_upload_max_memory_size,
            file_upload_max_memory_size=self.file_upload_max_memory_size,
            file_upload_temp_dir=self.file_upload_temp_dir,
            encoding=self.encoding
        )

        try:
            form, files = parser.parse()
        except (MultiPartParserError, RequestDataError) as e:
            raise ParseError("Couldn't parse multi-part data") from e

        result: ty.Dict[str, ty.List[ty.Any]] = {}
        result.update(form)
        result.update(files)

        return result


class FormParser(AbstractParser):

    media_types = ('application/x-www-form-urlencoded', 'application/x-url-encoded')

    def __init__(
            self,
            data_upload_max_number_fields: int = 1000,
            encoding: str = 'utf-8'
    ) -> None:
        self.data_upload_max_number_fields = data_upload_max_number_fields
        self.encoding = encoding

    def parse(self, stream: ty.IO, content_type: str, content_length: int) -> ty.Mapping[str, ty.Any]:
        form = MultiValueDict()
        parse_qsl_kwargs = {
            'keep_blank_values': True,
            'encoding': self.encoding,
            'fields_limit': self.data_upload_max_number_fields
        }
        query_string = stream.read()

        if isinstance(query_string, bytes):
            # query_string normally contains URL-encoded data, a subset of ASCII.
            try:
                query_string = query_string.decode('ascii')
            except UnicodeDecodeError:
                # ... but some user agents are misbehaving :-(
                query_string = query_string.decode('iso-8859-1')

        try:
            for key, value in limited_parse_qsl(query_string, **parse_qsl_kwargs):
                form.appendlist(key, value)
        except (ValueError, TypeError, RequestDataError) as e:
            raise ParseError("Couldn't parse form data") from e

        return form.dict()
