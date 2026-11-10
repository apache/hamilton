# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Decorators that stand in for a third-party library's wrappers.

``tests/resources/nodes_behind_wrappers.py`` decorates its functions with these. This module
must not define or import any name that module's annotations use (``Decimal``): the tests
rely on that name being absent here, as a user's names are absent from a real library.
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any


class DefinedOnlyInWrapperModule:
    """A type that only this module's namespace can resolve."""


def passthrough(fn: Callable) -> Callable:
    """The common case: a ``functools.wraps`` wrapper that keeps the signature."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    return wrapper


def fills_in(**fixed: Any) -> Callable[[Callable], Callable]:
    """Changes the signature: supplies some arguments and hides their parameters."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **fixed, **kwargs)

        signature = inspect.signature(fn)
        wrapper.__signature__ = signature.replace(
            parameters=[
                parameter for name, parameter in signature.parameters.items() if name not in fixed
            ]
        )
        return wrapper

    return decorator


def scaled_by_factor(fn: Callable) -> Callable:
    """Changes the signature and the annotations: adds an ``int`` parameter named ``factor``."""

    @functools.wraps(fn)
    def wrapper(*args: Any, factor: int, **kwargs: Any) -> Any:
        return fn(*args, **kwargs) * factor

    signature = inspect.signature(fn)
    wrapper.__signature__ = signature.replace(
        parameters=[
            *signature.parameters.values(),
            inspect.Parameter("factor", inspect.Parameter.KEYWORD_ONLY, annotation=int),
        ]
    )
    wrapper.__annotations__ = {**fn.__annotations__, "factor": int}
    return wrapper


def typed_without_wraps(fn: Callable) -> Callable:
    """No ``functools.wraps``: the wrapper's own annotations name a type of this module."""

    def typed_wrapper(
        value: "DefinedOnlyInWrapperModule",
    ) -> "DefinedOnlyInWrapperModule":
        return fn(value)

    return typed_wrapper


def untyped_without_wraps(fn: Callable) -> Callable:
    """No ``functools.wraps`` and no annotations: nothing tells Hamilton the types."""

    def untyped_wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return untyped_wrapper
