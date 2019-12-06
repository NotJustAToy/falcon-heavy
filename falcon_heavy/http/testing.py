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

import random
import string
import mimetypes
from io import BytesIO
from urllib.parse import urlencode

from falcon_heavy.utils import force_bytes

from .datastructures import MultiValueDict, FormStorage, FileStorage

__all__ = (
    'encode_multipart',
    'encode_urlencoded_form',
)

_BOUNDARY_CHARS = string.digits + string.ascii_letters


def encode_multipart(values, boundary=None, charset='utf-8'):
    """
    Encode values as multipart/form-data.

    """
    if boundary is None:
        boundary = ''.join(random.choice(_BOUNDARY_CHARS) for _ in range(30))

    body = BytesIO()
    write_binary = body.write

    def write(s):
        write_binary(s.encode(charset))

    if not isinstance(values, MultiValueDict):
        values = MultiValueDict(values)

    for key, values in values.lists():
        for value in values:
            write('--{0}\r\nContent-Disposition: form-data; name="{1}"'.format(boundary, key))

            if isinstance(value, FormStorage):
                write('\r\n')

                headers = value.headers.copy()

                content_type = value.content_type
                if content_type is not None:
                    headers['Content-Type'] = content_type

                for header in value.headers.items():
                    write('{0}: {1}\r\n'.format(*header))

                write('\r\n')

                value = value.value
                if not isinstance(value, str):
                    value = str(value)

                value = force_bytes(value, charset)
                write_binary(value)

            elif isinstance(value, FileStorage):
                filename = value.filename

                content_type = value.content_type
                if content_type is None:
                    content_type = (
                        filename and mimetypes.guess_type(filename)[0] or 'application/octet-stream')

                if filename is not None:
                    write('; filename="%s"\r\n' % filename)
                else:
                    write('\r\n')

                headers = value.headers.copy()
                headers['Content-Type'] = content_type

                for header in value.headers.items():
                    write('{0}: {1}\r\n'.format(*header))

                write('\r\n')

                while True:
                    chunk = value.read(16 * 1024)
                    if not chunk:
                        break

                    if isinstance(chunk, str):
                        chunk = force_bytes(chunk, charset)

                    write_binary(chunk)

            write('\r\n')

    write('--{0}--\r\n'.format(boundary))

    length = body.tell()
    body.seek(0)

    headers = {
        'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary),
        'Content-Length': str(length),
    }

    return body.read(), headers


def encode_urlencoded_form(values):
    """
    Encode values as application/x-www-form-urlencoded.

    """
    if not isinstance(values, MultiValueDict):
        values = MultiValueDict(values)

    body = urlencode(list(values.lists()), doseq=1)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    return body, headers
