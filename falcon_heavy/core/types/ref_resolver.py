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

import yaml
import json
import contextlib
import typing as ty
from collections import Sequence
from functools import lru_cache
from urllib.parse import urljoin, unquote, urldefrag, urlsplit as _urlsplit, urlparse, SplitResult
from urllib.request import urlopen

try:
    import requests
except ImportError:
    requests = None  # type: ignore

__all__ = (
    'RefResolutionError',
    'URIDict',
    'RefHandlers',
    'RefResolver',
)


class RefResolutionError(Exception):
    pass


def urlsplit(url: str) -> SplitResult:
    scheme, netloc, path, query, fragment = _urlsplit(url)
    if '#' in path:
        path, fragment = path.split('#', 1)
    return SplitResult(scheme, netloc, path, query, fragment)


VT = ty.TypeVar('VT')


class URIDict(ty.MutableMapping[str, VT]):
    """Dictionary which uses normalized URIs as keys."""

    @staticmethod
    def normalize(uri: str) -> str:
        return urlsplit(uri).geturl()

    def __init__(self, *args: ty.Any, **kwargs: ty.Any) -> None:
        self.store: ty.MutableMapping[str, VT] = dict()
        self.store.update(*args, **kwargs)

    def __getitem__(self, uri: str) -> ty.Any:
        return self.store[self.normalize(uri)]

    def __setitem__(self, uri: str, value: VT) -> None:
        self.store[self.normalize(uri)] = value

    def __delitem__(self, uri: str) -> None:
        del self.store[self.normalize(uri)]

    def __iter__(self) -> ty.Iterator[str]:
        return iter(self.store)

    def __len__(self) -> int:
        return len(self.store)

    def __repr__(self) -> str:
        return repr(self.store)


RefHandlers = ty.Mapping[str, ty.Callable[[str], ty.Mapping]]


class RefResolver:
    """
    Resolve JSON References.

    :param base_uri: URI of the referring document.
    :param referrer: The actual referring document.
    :param store: A mapping from URIs to documents to cache.
    :param cache_remote: Whether remote refs should be cached after
        first resolution.
    :param handlers: A mapping from URI schemes to functions that
        should be used to retrieve them.
    :param urljoin_cache: A cache that will be used for
        caching the results of joining the resolution scope to subscopes.
    :param remote_cache: A cache that will be used for
        caching the results of resolved remote URLs.
    """

    def __init__(
        self,
        base_uri: str,
        referrer: ty.Mapping,
        store: ty.Optional[ty.MutableMapping] = None,
        cache_remote: bool = True,
        handlers: ty.Optional[RefHandlers] = None,
        urljoin_cache: ty.Optional[ty.Callable] = None,
        remote_cache: ty.Optional[ty.Callable] = None,
    ):
        self.referrer = referrer
        self.cache_remote = cache_remote
        self.handlers = handlers or {}

        self._scopes_stack: ty.List[str] = [base_uri]
        self.store = URIDict[ty.Mapping]()
        if store is not None:
            self.store.update(store)
        self.store[base_uri] = referrer

        if urljoin_cache is None:
            urljoin_cache = lru_cache(1024)(urljoin)
        self._urljoin_cache = urljoin_cache

        if remote_cache is None:
            remote_cache = lru_cache(1024)(self.resolve_from_url)
        self._remote_cache = remote_cache

    def push_scope(self, scope: str) -> None:
        self._scopes_stack.append(
            self._urljoin_cache(self.resolution_scope, scope),
        )

    def pop_scope(self) -> None:
        try:
            self._scopes_stack.pop()
        except IndexError:
            raise RefResolutionError(
                "Failed to pop the scope from an empty stack. "
                "`pop_scope()` should only be called once for every "
                "`push_scope()`",
            )

    @property
    def resolution_scope(self) -> str:
        return self._scopes_stack[-1]

    @property
    def base_uri(self) -> str:
        uri, _ = urldefrag(self.resolution_scope)
        return uri

    @contextlib.contextmanager
    def in_scope(self, scope: str) -> ty.Generator:
        self.push_scope(scope)
        try:
            yield
        finally:
            self.pop_scope()

    @contextlib.contextmanager
    def resolving(self, ref: str) -> ty.Generator:
        """
        Context manager which resolves a JSON ``ref`` and enters the
        resolution scope of this ref.

        :param ref: Reference to resolve.
        """

        url, resolved = self.resolve(ref)
        self.push_scope(url)
        try:
            yield resolved
        finally:
            self.pop_scope()

    def resolve(self, ref: str) -> ty.Tuple[str, ty.Mapping]:
        url = self._urljoin_cache(self.resolution_scope, ref)
        return url, self._remote_cache(url)

    def resolve_from_url(self, url: str) -> ty.Mapping:
        url, fragment = urldefrag(url)
        try:
            document = self.store[url]
        except KeyError:
            try:
                document = self.resolve_remote(url)
            except Exception as exc:
                raise RefResolutionError(exc)

        return self.resolve_fragment(document, fragment)

    def resolve_fragment(self, document: ty.Mapping, fragment: str) -> ty.Mapping:
        """
        Resolve a ``fragment`` within the referenced ``document``.

        :param document: The referrant document.
        :param fragment: A URI fragment to resolve within it.
        :return: The resolved fragment.
        """

        fragment = fragment.lstrip('/')
        parts = unquote(fragment).split('/') if fragment else []

        for part in parts:
            part = part.replace('~1', '/').replace('~0', '~')

            if isinstance(document, Sequence):
                # Array indexes should be turned into integers
                try:
                    part = int(part)
                except ValueError:
                    pass
            try:
                document = document[part]
            except (TypeError, LookupError):
                raise RefResolutionError(
                    "Unresolvable JSON pointer: %r" % fragment
                )

        return document

    def resolve_remote(self, uri: str) -> ty.Mapping:
        """
        Resolve a remote ``uri``.

        If called directly, does not check the store first, but after
        retrieving the document at the specified URI it will be saved in
        the store if :attr:`cache_remote` is True.

        If the requests_ library is present, ``jsonschema`` will use it to
        request the remote ``uri``, so that the correct encoding is
        detected and used.

        If it isn't, or if the scheme of the ``uri`` is not ``http`` or
        ``https``, UTF-8 is assumed.

        :param uri: The URI to resolve.
        :return: The retrieved document.
        """

        scheme = urlsplit(uri).scheme

        if scheme in self.handlers:
            result = self.handlers[scheme](uri)

        elif (scheme in ['http', 'https'] and
              requests and
              getattr(requests.Response, 'json', None) is not None):
            # Requests has support for detecting the correct encoding of
            # json over http
            if callable(requests.Response.json):
                result = requests.get(uri).json()
            else:
                result = requests.get(uri).json

        elif scheme == 'file':
            path = urlparse(uri, 'file').path

            with open(path) as fh:
                try:
                    result = yaml.safe_load(fh)
                except yaml.YAMLError:
                    fh.seek(0)
                    try:
                        result = json.loads(fh.read())
                    except json.JSONDecodeError:
                        raise RefResolutionError(
                            "Unknown file format. Expected YAML or JSON")

        else:
            # Otherwise, pass off to urllib and assume utf-8
            result = json.loads(urlopen(uri).read().decode('utf-8'))

        if self.cache_remote:
            self.store[uri] = result

        return result
