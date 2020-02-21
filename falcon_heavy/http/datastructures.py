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
import copy
import errno
import typing as ty

__all__ = (
    'MultiValueDictKeyError',
    'MultiValueDict',
    'FormStorage',
    'FileStorage',
)


class MultiValueDictKeyError(KeyError):
    pass


class MultiValueDict(dict):
    """
    A subclass of dictionary customized to handle multiple values for the
    same key.

    This class exists to solve the irritating problem raised by cgi.parse_qs,
    which returns a list for every key, even though most Web forms submit
    single name-value pairs.
    """
    def __init__(self, mapping=()):
        if isinstance(mapping, MultiValueDict):
            super(MultiValueDict, self).__init__(((k, l[:]) for k, l in mapping.lists()))
        elif isinstance(mapping, dict):
            tmp = {}
            for key, value in mapping.items():
                if isinstance(value, (tuple, list)):
                    if len(value) == 0:
                        continue
                    value = list(value)
                else:
                    value = [value]
                tmp[key] = value
            super(MultiValueDict, self).__init__(tmp)
        else:
            tmp = {}
            for key, value in mapping or ():
                tmp.setdefault(key, []).append(value)
            super(MultiValueDict, self).__init__(tmp)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             super(MultiValueDict, self).__repr__())

    def __getitem__(self, key):
        """
        Returns the last data value for this key, or [] if it's an empty list;
        raises KeyError if not found.
        """
        try:
            list_ = super(MultiValueDict, self).__getitem__(key)
        except KeyError:
            raise MultiValueDictKeyError(repr(key))
        try:
            return list_[-1]
        except IndexError:
            return []

    def __setitem__(self, key, value):
        super(MultiValueDict, self).__setitem__(key, [value])

    def __copy__(self):
        return self.__class__([
            (k, v[:])
            for k, v in self.lists()
        ])

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        result = self.__class__()
        memo[id(self)] = result
        for key, value in dict.items(self):
            dict.__setitem__(
                result, copy.deepcopy(key, memo), copy.deepcopy(value, memo))
        return result

    def __getstate__(self):
        obj_dict = self.__dict__.copy()
        obj_dict['_data'] = {k: self._getlist(k) for k in self}
        return obj_dict

    def __setstate__(self, obj_dict):
        data = obj_dict.pop('_data', {})
        for k, v in data.items():
            self.setlist(k, v)
        self.__dict__.update(obj_dict)

    def get(self, key, default=None):
        """
        Returns the last data value for the passed key. If key doesn't exist
        or value is an empty list, then default is returned.
        """
        try:
            val = self[key]
        except KeyError:
            return default
        if not val:
            return default
        return val

    def _getlist(self, key, default=None, force_list=False):
        """
        Return a list of values for the key.
        Used internally to manipulate values list. If force_list is True,
        return a new copy of values.
        """
        try:
            values = super(MultiValueDict, self).__getitem__(key)
        except KeyError:
            if default is None:
                return []
            return default
        else:
            if force_list:
                values = list(values) if values is not None else None
            return values

    def getlist(self, key, default=None):
        """
        Return the list of values for the key. If key doesn't exist, return a
        default value.
        """
        return self._getlist(key, default, force_list=True)

    def setlist(self, key, list_):
        super(MultiValueDict, self).__setitem__(key, list_)

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
            # Do not return default here because __setitem__() may store
            # another value -- QueryDict.__setitem__() does. Look it up.
        return self[key]

    def setlistdefault(self, key, default_list=None):
        if key not in self:
            if default_list is None:
                default_list = []
            self.setlist(key, default_list)
            # Do not return default_list here because setlist() may store
            # another value -- QueryDict.setlist() does. Look it up.
        return self._getlist(key)

    def appendlist(self, key, value):
        """Appends an item to the internal list associated with key."""
        self.setlistdefault(key).append(value)

    def items(self):
        """
        Yields (key, value) pairs, where value is the last item in the list
        associated with the key.
        """
        for key in self:
            yield key, self[key]

    def lists(self):
        """Yields (key, list) pairs."""
        return super(MultiValueDict, self).items()

    def values(self):
        """Yield the last value on every key list."""
        for key in self:
            yield self[key]

    def copy(self):
        """Returns a shallow copy of this object."""
        return copy.copy(self)

    def update(self, *args, **kwargs):
        """
        update() extends rather than replaces existing key lists.
        Also accepts keyword args.
        """
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        if args:
            other_dict = args[0]
            if isinstance(other_dict, MultiValueDict):
                for key, value_list in other_dict.lists():
                    self.setlistdefault(key).extend(value_list)
            else:
                try:
                    for key, value in other_dict.items():
                        self.setlistdefault(key).append(value)
                except TypeError:
                    raise ValueError("MultiValueDict.update() takes either a MultiValueDict or dictionary")
        for key, value in kwargs.items():
            self.setlistdefault(key).append(value)

    def dict(self):
        """
        Returns current object as a dict with singular values.
        """
        return {key: self.getlist(key)[0] if len(self.getlist(key)) == 1 else self.getlist(key) for key in self}


class FormStorage:

    def __init__(
            self,
            value: str,
            content_type: ty.Optional[str] = None,
            headers: ty.Optional[ty.MutableMapping[str, str]] = None
    ) -> None:
        self.value = value
        if headers is None:
            headers = {}
        if content_type is not None:
            headers['content-type'] = content_type
        self.headers = headers

    @property
    def content_type(self) -> ty.Optional[str]:
        return self.headers.get('content-type')


class FileStorage:

    def __init__(
            self,
            stream: ty.IO,
            filename: ty.Optional[str] = None,
            content_type: ty.Optional[str] = None,
            content_length: ty.Optional[int] = None,
            headers: ty.Optional[ty.MutableMapping[str, str]] = None
    ) -> None:
        self.stream = stream
        self._filename = filename
        if headers is None:
            headers = {}
        self.headers = headers
        if content_type is not None:
            headers['content-type'] = content_type
        if content_length is not None:
            headers['content-length'] = str(content_length)

    @property
    def filename(self) -> ty.Optional[str]:
        # Sanitize the file name so that it can't be dangerous.
        filename = self._filename
        if filename is not None:
            # Just use the basename of the file -- anything else is dangerous.
            filename = os.path.basename(filename)

            # File names longer than 255 characters can cause problems on older OSes.
            if len(filename) > 255:
                filename, ext = os.path.splitext(filename)
                ext = ext[:255]
                filename = filename[:255 - len(ext)] + ext

        return filename

    @filename.setter
    def filename(self, filename: str) -> None:
        self._filename = filename

    @property
    def content_type(self) -> ty.Optional[str]:
        return self.headers.get('content-type')

    @property
    def content_length(self) -> int:
        return int(self.headers.get('content-length') or 0)

    def read(self, size: int = -1) -> ty.AnyStr:
        return self.stream.read(size)

    def save(self, dst: ty.Union[str, ty.IO], buffer_size: int = 16 * 1024) -> None:
        """Save the file to a destination path or file object.  If the
        destination is a file object you have to close it yourself after the
        call.  The buffer size is the number of bytes held in memory during
        the copy process.  It defaults to 16KB.

        For secure file saving also have a look at :func:`secure_filename`.

        :param dst: a filename or open file object the uploaded file
            is saved to.
        :param buffer_size: the size of the buffer.  This works the same as
            the `length` parameter of :func:`shutil.copyfileobj`.
        """
        from shutil import copyfileobj
        close_dst = False
        if isinstance(dst, str):
            dst = open(dst, 'wb')
            close_dst = True
        try:
            copyfileobj(self.stream, dst, buffer_size)
        finally:
            if close_dst:
                dst.close()

    def close(self) -> None:
        """Close the underlying file if possible."""
        try:
            return self.stream.close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                # Means the file was moved or deleted before the tempfile
                # could unlink it.  Still sets self.file.close_called and
                # calls self.file.file.close() before the exception
                raise

    def __nonzero__(self) -> bool:
        return bool(self.filename)

    __bool__ = __nonzero__

    def __iter__(self) -> ty.Iterator:
        return iter(self.stream)
