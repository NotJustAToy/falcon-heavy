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

import re
import typing as ty
from urllib.parse import unquote
from html import entities as html_entities

from falcon_heavy.utils import force_str

from .exceptions import TooManyFieldsSent

__all__ = (
    'limited_parse_qsl',
    'parse_header',
    'ContentTypeLikeHeader',
    'parse_options_header',
    'unescape_entities',
)

FIELDS_MATCH = re.compile('[&;]')


def limited_parse_qsl(qs, keep_blank_values=False, encoding='utf-8',
                      errors='replace', fields_limit=None):
    """
    Return a list of key/value tuples parsed from query string.
    Copied from urlparse with an additional "fields_limit" argument.
    Copyright (C) 2013 Python Software Foundation (see LICENSE.python).

    :param qs: percent-encoded query string to be parsed
    :param keep_blank_values: flag indicating whether blank values in
        percent-encoded queries should be treated as blank strings. A
        true value indicates that blanks should be retained as blank
        strings. The default false value indicates that blank values
        are to be ignored and treated as if they were  not included
    :param encoding: specify how to decode percent-encoded sequences
        into Unicode characters, as accepted by the bytes.decode() method
    :param errors: may be given to set the desired error handling scheme
    :param fields_limit: maximum number of fields parsed or an exception
        is raised. None means no limit and is the default
    """
    if fields_limit:
        pairs = FIELDS_MATCH.split(qs, fields_limit)
        if len(pairs) > fields_limit:
            raise TooManyFieldsSent("Too many GET/POST parameters")
    else:
        pairs = FIELDS_MATCH.split(qs)
    r = []
    for name_value in pairs:
        if not name_value:
            continue
        nv = name_value.split(str('='), 1)
        if len(nv) != 2:
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = nv[0].replace('+', ' ')
            name = unquote(name, encoding=encoding, errors=errors)
            value = nv[1].replace('+', ' ')
            value = unquote(value, encoding=encoding, errors=errors)
            r.append((name, value))
    return r


def parse_header(line):
    """
    Parse the header into a name-value.
    """
    parts = line.split(b':', 1)

    if len(parts) == 2:
        return parts[0].lower().strip().decode('ascii'), parts[1].strip()

    else:
        raise ValueError("Invalid header: %r" % line)


class ContentTypeLikeHeader(ty.NamedTuple):

    mimetype: str
    params: ty.Mapping[str, str] = {}

    def __str__(self) -> str:
        parts = [self.mimetype]
        for name, value in self.params.items():
            parts.append('%s=%s' % (name, value))
        return '; '.join(parts)


def parse_options_header(value, encoding='utf-8', errors='strict'):
    """Parse a Content-Type like header"""
    parts = _split_header_params(b';' + value)
    mimetype = parts.pop(0).lower().decode('ascii')
    params = {}
    for part in parts:
        i = part.find(b'=')
        if i >= 0:
            has_encoding = False
            name = part[:i].strip().lower().decode('ascii')
            if name.endswith('*'):
                # Lang/encoding embedded in the value (like "filename*=UTF-8''file.ext")
                # http://tools.ietf.org/html/rfc2231#section-4
                name = name[:-1]
                if part.count(b"'") == 2:
                    has_encoding = True
            value = part[i + 1:].strip()
            if has_encoding:
                encoding, lang, value = value.split(b"'")
                value = unquote(value.decode(), encoding=encoding.decode())
            if len(value) >= 2 and value[:1] == value[-1:] == b'"':
                value = value[1:-1]
                value = value.replace(b'\\\\', b'\\').replace(b'\\"', b'"')
            params[name] = force_str(value, encoding=encoding, errors=errors)
    return ContentTypeLikeHeader(mimetype, params)


def _split_header_params(s):
    """Split header parameters."""
    result = []
    while s[:1] == b';':
        s = s[1:]
        end = s.find(b';')
        while end > 0 and s.count(b'"', 0, end) % 2:
            end = s.find(b';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        result.append(f.strip())
        s = s[end:]
    return result


def _replace_entity(match):
    text = match.group(1)
    if text[0] == '#':
        text = text[1:]
        try:
            if text[0] in 'xX':
                c = int(text[1:], 16)
            else:
                c = int(text)
            return chr(c)
        except ValueError:
            return match.group(0)
    else:
        try:
            return chr(html_entities.name2codepoint[text])
        except (ValueError, KeyError):
            return match.group(0)


_entity_re = re.compile(r"&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));")


def unescape_entities(text):
    return _entity_re.sub(_replace_entity, force_str(text))
