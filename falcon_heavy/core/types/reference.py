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
from collections import Mapping

from wrapt import ObjectProxy

from .base import AbstractConvertible, Messages
from .ref_resolver import RefResolver, RefResolutionError
from .exceptions import SchemaError
from .errors import Error
from .path import Path

__all__ = (
    'Registry',
    'VisitedRefs',
    'ReferenceType',
)


class RecursiveReferenceError(Exception):
    pass


Bad = object()
Dummy = object()


Registry = ty.Dict[Path, ty.Any]
VisitedRefs = ty.Set[Path]


T = ty.TypeVar('T')


class ReferenceType(AbstractConvertible[T]):

    """Reference type

    Serves for resolving references and storing converted data in the registry

    :param subtype: referenced type
    """

    MESSAGES: ty.ClassVar[Messages] = {
        'bad_reference': "$refs must reference a valid location in the document",
        'recursive_reference': "Recursive reference was found",
        'unresolvable_reference': "Couldn't resolve reference"
    }

    __slots__ = ('subtype', )

    def __init__(self, subtype: AbstractConvertible[T], **kwargs: ty.Any) -> None:
        self.subtype = subtype
        super(ReferenceType, self).__init__(**kwargs)

    @staticmethod
    def _get_ref(value: ty.Any) -> ty.Optional[str]:
        ref = None
        if isinstance(value, Mapping) and '$ref' in value:
            ref = value['$ref']
        return ref

    def _entry(
            self,
            value: ty.Any,
            path: Path,
            visited_refs: ty.Optional[VisitedRefs] = None,
            registry: ty.Optional[Registry] = None,
            **context: ty.Any
    ) -> ty.Any:
        ref = self._get_ref(value)

        if ref is not None:
            return self._dive(
                ref, path, visited_refs=visited_refs, registry=registry, **context)

        else:
            assert registry is not None
            result = registry.get(path)

            if result is Bad:
                pass

            elif result is not None:
                return result

            proxy = ObjectProxy(Dummy)
            registry[path] = proxy
            try:
                result = self.subtype.convert(
                    value,
                    path,
                    registry=registry,
                    **context
                )
            except SchemaError:
                registry[path] = Bad
                raise

            else:
                proxy.__wrapped__ = weakref.proxy(result)
                registry[path] = result

            return result

    def _dive(
            self,
            ref: str,
            path: Path,
            visited_refs: ty.Optional[VisitedRefs] = None,
            ref_resolver: ty.Optional[RefResolver] = None,
            registry: ty.Optional[Registry] = None,
            **context: ty.Any
    ) -> ty.Any:
        visited_refs = visited_refs or set()

        assert ref_resolver is not None
        assert registry is not None

        try:
            with ref_resolver.resolving(ref) as target:
                target_path = Path(ref_resolver.resolution_scope)

                if target_path in visited_refs:
                    raise RecursiveReferenceError()

                result = registry.get(target_path)

                if result is Bad:
                    raise SchemaError(Error(path, self.messages['bad_reference']))

                elif result is not None:
                    return result

                proxy = ObjectProxy(Dummy)
                registry[target_path] = proxy
                visited_refs.add(target_path)
                try:
                    result = self._deeper(
                        target,
                        target_path,
                        visited_refs=visited_refs,
                        ref_resolver=ref_resolver,
                        registry=registry,
                        **context
                    )
                except SchemaError as e:
                    registry[target_path] = Bad
                    raise SchemaError(Error(path, self.messages['bad_reference']), *e.errors)

                except RecursiveReferenceError:
                    registry[target_path] = Bad
                    raise SchemaError(Error(path, self.messages['recursive_reference']))

                else:
                    proxy.__wrapped__ = weakref.proxy(result)
                    registry[target_path] = result

                finally:
                    visited_refs.discard(target_path)

                return result

        except RefResolutionError:
            raise SchemaError(Error(path, self.messages['unresolvable_reference']))

    def _deeper(
            self,
            value: ty.Any,
            path: Path,
            visited_refs: ty.Optional[VisitedRefs] = None,
            **context: ty.Any
    ) -> ty.Any:
        ref = self._get_ref(value)

        if ref is not None:
            return self._dive(
                ref, path, visited_refs=visited_refs, **context)

        else:
            return self.subtype.convert(value, path, **context)

    def convert(self, value: ty.Any, path: Path, *args: ty.Any, **context: ty.Any) -> T:
        return self._entry(value, path, **context)
