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
import base64
import binascii
import cgi
import typing as ty
from collections import Iterator

from falcon_heavy.utils import force_str, force_bytes

from .datastructures import MultiValueDict, FormStorage, FileStorage
from .utils import parse_header, parse_options_header, unescape_entities
from .exceptions import (
    RequestDataTooBig,
    TooManyFieldsSent
)

SpooledTemporaryFile: ty.Any

try:
    from tempfile import SpooledTemporaryFile
except ImportError:
    from tempfile import TemporaryFile
    SpooledTemporaryFile = None

__all__ = (
    'MultiPartParserError',
    'MultiPartParser',
)


class MultiPartParserError(Exception):
    pass


_BASE64_DECODE_ERROR = binascii.Error


class MultiPartParser:
    """
    A rfc2388 multipart/form-data parser.

    ``MultiValueDict.parse()`` reads the input stream in ``chunk_size`` chunks
    and returns a tuple of ``(MultiValueDict(FORM), MultiValueDict(FILES))``.

    :param stream: the raw post data, as a file-like object
    :param content_type: content type that contains boundary
    :param content_length: length of content in bytes
    :param data_upload_max_number_fields: maximum number of parameters
        that will be read before a SuspiciousOperation (TooManyFieldsSent) is raised
    :param data_upload_max_memory_size: the maximum number of bytes to be accepted
        for in-memory stored form data
    :param file_upload_max_memory_size: maximum size in bytes of request data
        (excluding file uploads) that will be read before a
        SuspiciousOperation (RequestDataTooBig) is raised
    :param file_upload_temp_dir: directory in which upload streamed files will
        be temporarily saved. If `None` then used the operating system's default
        temporary directory (i.e. "/tmp" on *nix systems)
    :param chunk_size: the number of bytes that will be read at a time
    :param encoding: the encoding with which to treat the incoming data
    """

    def __init__(self,
                 stream,
                 content_type,
                 content_length,
                 data_upload_max_number_fields=1000,
                 data_upload_max_memory_size=2621440,
                 file_upload_max_memory_size=2621440,
                 file_upload_temp_dir=None,
                 chunk_size=64 * 1024,
                 encoding='utf-8'):
        # Content-Type should contain multipart and the boundary information.
        if not content_type.startswith('multipart/'):
            raise MultiPartParserError('Invalid Content-Type: %s' % content_type)

        # Parse the header to get the boundary to split the parts.
        boundary = parse_options_header(force_bytes(
            content_type, encoding='ascii')).params.get('boundary')
        if not boundary or not cgi.valid_boundary(boundary):
            raise MultiPartParserError('Invalid boundary in multipart: %s' % boundary)

        if content_length < 0:
            # This means we shouldn't continue...raise an error.
            raise MultiPartParserError("Invalid content length: %r" % content_length)

        self._boundary = force_bytes(boundary, encoding='ascii')
        self._stream = stream

        self._chunk_size = (chunk_size // 4 + 1) * 4

        self._data_upload_max_number_fields = data_upload_max_number_fields
        self._data_upload_max_memory_size = data_upload_max_memory_size

        self._file_upload_temp_dir = file_upload_temp_dir
        self._file_upload_max_memory_size = file_upload_max_memory_size

        self._encoding = encoding

        self._content_length = content_length

    def new_file_stream(self, total_content_length):
        if SpooledTemporaryFile is not None:
            return SpooledTemporaryFile(
                max_size=self._file_upload_max_memory_size,
                suffix='.upload',
                mode='wb+',
                dir=self._file_upload_temp_dir
            )

        if (
                total_content_length is None or
                total_content_length > self._file_upload_max_memory_size
        ):
            return TemporaryFile(
                suffix='.upload',
                mode='wb+',
                dir=self._file_upload_temp_dir
            )

        return io.BytesIO()

    def parse(self):
        """
        Parse the POST data and break it into a FILES MultiValueDict and a POST
        MultiValueDict.

        Return a tuple containing the POST and FILES dictionary, respectively.
        """
        encoding = self._encoding

        # HTTP spec says that Content-Length >= 0 is valid
        # handling content-length == 0 before continuing
        if self._content_length == 0:
            return MultiValueDict(), MultiValueDict()

        # Create the data structures to be used later.
        form = MultiValueDict()
        files = MultiValueDict()

        # Instantiate the parser and stream:
        stream = LazyStream(chunk_iter(self._stream, self._chunk_size))

        # Number of bytes that have been read.
        num_bytes_read = 0
        # To count the number of keys in the request.
        num_post_keys = 0
        # To limit the amount of data read from the request.
        read_size = None

        parts = part_iter(stream, self._boundary)

        # Find first boundary
        try:
            exhaust(next(parts))
        except MultiPartParserError as e:
            raise MultiPartParserError("Expected boundary at start of multipart data") from e

        for part in parts:
            # Stream at beginning of header, look for end of header
            # and parse it if found.
            chunks = []
            previous = b''
            for chunk in part:
                # 'find' returns the top of these four bytes, so we'll
                # need to munch them later to prevent them from polluting
                # the payload.
                if previous:
                    chunk = previous + chunk

                header_end = chunk.find(b'\r\n\r\n')

                if header_end < 0:
                    # We find no header
                    previous = chunk[-4:]
                    chunks.append(chunk[:-4])
                    continue

                else:
                    chunks.append(chunk[:header_end])
                    # here we place any excess chunk back onto the stream, as
                    # well as throwing away the CRLFCRLF bytes from above.
                    part.unget(chunk[header_end + 4:])
                    break

            header = b''.join(chunks)

            if not header:
                continue

            content_disposition = None
            content_type = None

            headers = {}
            for line in header.split(b'\r\n'):
                try:
                    name, value = parse_header(line)
                except ValueError:
                    continue

                if name in 'content-disposition':
                    content_disposition = parse_options_header(
                        value, encoding=encoding, errors='replace')

                elif name == 'content-type':
                    content_type = parse_options_header(
                        value, encoding=encoding, errors='replace')

                else:
                    headers[name] = force_str(
                        value, encoding=encoding, errors='replace')

            if content_disposition is None:
                continue

            headers['content-disposition'] = str(content_disposition)

            if content_type is not None:
                headers['content-type'] = str(content_type)

            field_name = content_disposition.params.get('name')
            if field_name is None:
                continue

            transfer_encoding = headers.get('content-transfer-encoding')

            filename = content_disposition.params.get('filename')
            if filename:
                filename = self.ie_sanitize(unescape_entities(filename))

                if not filename:
                    continue

                stream = self.new_file_stream(self._content_length)

                for chunk in part:
                    if transfer_encoding == 'base64':
                        # We only special-case base64 transfer encoding
                        # We should always decode base64 chunks by multiple of 4,
                        # ignoring whitespace

                        stripped_chunk = b''.join(chunk.split())

                        remaining = len(stripped_chunk) % 4
                        while remaining != 0:
                            over_chunk = part.read(4 - remaining)
                            if not over_chunk:
                                break
                            stripped_chunk += b''.join(over_chunk.split())
                            remaining = len(stripped_chunk) % 4

                        try:
                            chunk = base64.b64decode(stripped_chunk)
                        except Exception as e:
                            # Since this is only a chunk, any error is an unfixable error
                            raise MultiPartParserError("Could not decode base64 data: %s" % e) from e

                    stream.write(chunk)

                stream.seek(0)
                files.appendlist(field_name, FileStorage(
                    stream=stream,
                    filename=filename,
                    headers=headers
                ))

            else:
                num_post_keys += 1
                if (self._data_upload_max_number_fields is not None and
                        self._data_upload_max_number_fields < num_post_keys):
                    raise TooManyFieldsSent("Too many GET/POST parameters")

                if self._data_upload_max_memory_size is not None:
                    read_size = self._data_upload_max_memory_size - num_bytes_read

                # This is a post field, we can just set it in the post
                if transfer_encoding == 'base64':
                    raw_data = part.read(size=read_size)
                    num_bytes_read += len(raw_data)
                    try:
                        data = base64.b64decode(raw_data)
                    except _BASE64_DECODE_ERROR:
                        data = raw_data

                else:
                    data = part.read(size=read_size)
                    num_bytes_read += len(data)

                # Add two here to make the check consistent with the
                # x-www-form-urlencoded check that includes '&='
                num_bytes_read += len(field_name) + 2
                if (self._data_upload_max_memory_size is not None and
                        num_bytes_read > self._data_upload_max_memory_size):
                    raise RequestDataTooBig('Too big request body')

                form.appendlist(field_name, FormStorage(
                    value=force_str(data, encoding, errors='replace'),
                    headers=headers
                ))

        # Make sure that the request data is all fed
        exhaust(self._stream)

        return form, files

    @staticmethod
    def ie_sanitize(filename):
        """Cleanup filename from Internet Explorer full paths."""
        return filename and filename[filename.rfind('\\') + 1:].strip()


class LazyStream(Iterator):
    """
    The LazyStream wrapper allows one to get and "unget" bytes from a stream.

    Given a producer object (an iterator that yields bytestrings), the
    LazyStream object will support iteration, reading, and keeping a "look-back"
    variable in case you need to "unget" some bytes.
    """
    def __init__(self, producer, length=None):
        """
        Every LazyStream must have a producer when instantiated.

        A producer is an iterable that returns a string each time it
        is called.
        """
        self._producer = producer
        self._empty = False
        self._leftover = b''
        self.length = length
        self.position = 0
        self._remaining = length

    def tell(self):
        return self.position

    def read(self, size=None):
        def parts():
            remaining = self._remaining if size is None else size
            # do the whole thing in one shot if no limit was provided.
            if remaining is None:
                yield b''.join(self)
                return

            # otherwise do some bookkeeping to return exactly enough
            # of the stream and stashing any extra content we get from
            # the producer
            while remaining != 0:
                assert remaining > 0, 'remaining bytes to read should never go negative'

                try:
                    chunk = next(self)
                except StopIteration:
                    return
                else:
                    emitting = chunk[:remaining]
                    self.unget(chunk[remaining:])
                    remaining -= len(emitting)
                    yield emitting

        out = b''.join(parts())
        return out

    def __next__(self):
        """
        Used when the exact number of bytes to read is unimportant.

        This procedure just returns whatever is chunk is conveniently returned
        from the iterator instead. Useful to avoid unnecessary bookkeeping if
        performance is an issue.
        """
        if self._leftover:
            output = self._leftover
            self._leftover = b''
        else:
            output = next(self._producer)
        self.position += len(output)
        return output

    def close(self):
        """
        Used to invalidate/disable this lazy stream.

        Replaces the producer with an empty list. Any leftover bytes that have
        already been read will still be reported upon read() and/or next().
        """
        self._producer = []

    def __iter__(self):
        return self

    def unget(self, chunk):
        """
        Places bytes back onto the front of the lazy stream.

        Future calls to read() will return those bytes first. The
        stream position and thus tell() will be rewound.
        """
        if not chunk:
            return
        self.position -= len(chunk)
        self._leftover = b''.join([chunk, self._leftover])


def chunk_iter(flo, chunk_size=64 * 1024):
    """An iterable that will yield chunks of data."""
    while True:
        chunk = flo.read(chunk_size)

        if not chunk:
            break

        yield chunk


def part_iter(stream, boundary):
    """
    A Producer that will iterate over boundaries.
    """
    delimiter = b'--' + boundary
    delimiter_length = len(delimiter)

    while True:
        # Check that the stream is already exhausted
        unused_char = stream.read(1)

        if not unused_char:
            raise MultiPartParserError("Unexpected end of multipart data")

        stream.unget(unused_char)

        part = LazyStream(boundary_iter(stream, delimiter))

        try:
            yield part
        finally:
            exhaust(part)

        data = stream.read(delimiter_length + 2)

        if data[-2:] == b'--':
            exhaust(stream)
            break

        if data[-2:] != b'\r\n':
            stream.unget(data[-2:])


def boundary_iter(stream, delimiter):
    """
    A Producer that is sensitive to boundaries.

    Will happily yield bytes until a boundary is found. Will yield
    the bytes before the boundary and push the boundary and the
    post-boundary bytes back on the stream.

    The future calls to next() after locating the boundary will raise a
    `StopIteration` exception.

    Raises `MultiPartParserError` if unexpected end of part will found.
    """
    delimiter_length = len(delimiter)

    while True:
        bytes_read = 0
        chunks = []
        for chunk in stream:
            if not chunk:
                break

            bytes_read += len(chunk)
            chunks.append(chunk)

            if bytes_read > delimiter_length:
                break

        data = b''.join(chunks)

        # Find a parts delimiter in data
        index = data.find(delimiter)
        if index < 0:
            output = data[:-delimiter_length]
            if not output:
                raise MultiPartParserError("Unexpected end of part")
            else:
                # Make sure we don't treat a partial delimiter as data
                stream.unget(data[-delimiter_length:])
                yield output
        else:
            stream.unget(data[index:])

            # Backup over CRLF
            last = max(0, index - 1)
            if data[last:last + 1] == b'\n':
                index -= 1
            last = max(0, index - 1)
            if data[last:last + 1] == b'\r':
                index -= 1

            yield data[:index]
            break


def exhaust(stream, chunk_size=16 * 1024):
    """Exhaust a stream."""
    iterator = chunk_iter(stream, chunk_size)

    for _ in iterator:
        pass
