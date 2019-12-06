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

import itertools
import typing as ty

__all__ = (
    'unbool',
    'uniq',
    'is_file_like',
)


def unbool(element: ty.Any, true: object = object(), false: object = object()) -> ty.Any:
    """A hack to make True and 1 and False and 0 unique for ``uniq``"""

    if element is True:
        return true
    elif element is False:
        return false
    return element


def uniq(container: ty.Sequence) -> bool:
    """Check if all of a container's elements are unique

    Successively tries first to rely that the elements are hashable, then
    falls back on them being sortable, and finally falls back on brute
    force
    """

    try:
        return len(set(unbool(i) for i in container)) == len(container)
    except TypeError:
        try:
            sort = sorted(unbool(i) for i in container)
            sliced = itertools.islice(sort, 1, None)
            for i, j in zip(sort, sliced):
                if i == j:
                    return False
        except (NotImplementedError, TypeError):
            seen: ty.List = []
            for e in container:
                e = unbool(e)
                if e in seen:
                    return False
                seen.append(e)
    return True


def is_file_like(o: ty.Any) -> bool:
    """Check if ``o`` is file-like object"""
    try:
        o.read(0)
    except (AttributeError, TypeError):
        return False

    return True
