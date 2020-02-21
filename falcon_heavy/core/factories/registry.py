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

import weakref
import typing as ty
from functools import wraps

from falcon_heavy.core import types as t

__all__ = (
    'hashkey',
    'registered',
)


class ProxyType(t.AbstractConvertible):

    __slots__ = ('wrapped', )

    def __init__(self, wrapped: ty.Optional[t.AbstractConvertible] = None, **kwargs: ty.Any) -> None:
        self.wrapped = wrapped
        super(ProxyType, self).__init__(**kwargs)

    def convert(self, value: ty.Any, path: t.Path, *args: ty.Any, **context: ty.Any) -> ty.Any:
        assert self.wrapped is not None, "Wrapped type must be specified"

        return self.wrapped.convert(value, path, **context)


kwd_mark = (object(),)


def hashkey(*args: ty.Any, **kwargs: ty.Any) -> ty.Hashable:
    """Return a cache key for the specified hashable arguments"""

    key = args
    if kwargs:
        key += kwd_mark + tuple(sorted(kwargs.items()))

    return key


def registered(key: ty.Callable = hashkey) -> ty.Callable:
    """Registered decorator

    Stores generated types in the registry. Allow recursive generation
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            k = key(*args, **kwargs)
            try:
                registry = self.__registry
            except AttributeError:
                registry = self.__registry = {}
            result = registry.get(k)
            if result is not None:
                return result
            proxy = ProxyType()
            registry[k] = proxy
            result = method(self, *args, **kwargs)
            proxy.wrapped = weakref.proxy(result)
            registry[k] = result
            return result
        return wrapper
    return decorator
