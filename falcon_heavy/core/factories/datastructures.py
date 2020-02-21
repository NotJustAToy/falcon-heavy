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

from collections import MutableMapping

__all__ = (
    'TransformDict',
    'CaseInsensitiveDict',
)

_sentinel = object()


class TransformDict(MutableMapping):
    """Dictionary that calls a transformation function when looking
    up keys, but preserves the original keys.
    >>> d = TransformDict(str.lower)
    >>> d['Foo'] = 5
    >>> d['foo'] == d['FOO'] == d['Foo'] == 5
    True
    >>> set(d.keys())
    {'Foo'}
    """

    __slots__ = ('_transform', '_original', '_data')

    def __init__(self, transform, mapping=None, **kwargs):
        self._transform = transform
        self._original = {}
        self._data = {}
        if mapping is not None:
            self.update(mapping)
        if kwargs:
            self.update(kwargs)

    def getitem(self, key):
        transformed = self._transform(key)
        original = self._original[transformed]
        value = self._data[transformed]
        return original, value

    @property
    def transform_func(self):
        return self._transform

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._original.values())

    def __getitem__(self, key):
        return self._data[self._transform(key)]

    def __setitem__(self, key, value):
        transformed = self._transform(key)
        self._data[transformed] = value
        self._original.setdefault(transformed, key)

    def __delitem__(self, key):
        transformed = self._transform(key)
        del self._data[transformed]
        del self._original[transformed]

    def clear(self):
        self._data.clear()
        self._original.clear()

    def __contains__(self, key):
        return self._transform(key) in self._data

    def get(self, key, default=None):
        return self._data.get(self._transform(key), default)

    def pop(self, key, default=_sentinel):
        transformed = self._transform(key)

        if default is _sentinel:
            del self._original[transformed]
            return self._data.pop(transformed)

        else:
            self._original.pop(transformed, None)
            return self._data.pop(transformed, default)

    def popitem(self):
        transformed, value = self._data.popitem()
        return self._original.pop(transformed), value

    def copy(self):
        other = self.__class__(self._transform)
        other._original = self._original.copy()
        other._data = self._data.copy()
        return other

    __copy__ = copy

    def __getstate__(self):
        return self._transform, self._data, self._original

    def __setstate__(self, state):
        self._transform, self._data, self._original = state

    def __repr__(self):
        try:
            equiv = dict(self)
        except TypeError:
            # Some keys are unhashable, fall back on .items()
            equiv = list(self.items())
        return '%s(%r, %s)' % (self.__class__.__name__, self._transform, repr(equiv))


class CaseInsensitiveDict(TransformDict):

    def __init__(self, mapping=None, **kwargs):
        super(CaseInsensitiveDict, self).__init__(str.lower, mapping=mapping, **kwargs)
