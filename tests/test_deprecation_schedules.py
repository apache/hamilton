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

"""How Hamilton's own deprecations reach users: on the release clock, as warnings users can filter."""

import ast
import dataclasses
import inspect
import pathlib
import warnings

import pandas as pd
import pytest

import hamilton
from hamilton import models
from hamilton.dev_utils import deprecation
from hamilton.dev_utils.deprecation import DeprecationError, Version, deprecated
from hamilton.function_modifiers import macros

_DEPRECATED = "hamilton.dev_utils.deprecation.deprecated"
_CURRENT_VERSION_POSITION = [field.name for field in dataclasses.fields(deprecated)].index(
    "current_version"
)


def _deprecated_calls(tree: ast.Module, module: str, is_package: bool = False) -> list[ast.Call]:
    """Every call of ``hamilton.dev_utils.deprecation.deprecated`` in a module, whatever name or
    import form (absolute, relative, aliased, or reached through a parent module) it is called by."""
    package = module if is_package else module.rpartition(".")[0]
    bound = {}  # name in this module -> the dotted name it refers to
    for statement in ast.walk(tree):
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.asname:
                    bound[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    bound[root] = root
        elif isinstance(statement, ast.ImportFrom):
            source = statement.module or ""
            if statement.level:
                base = package
                for _ in range(statement.level - 1):
                    base = base.rpartition(".")[0]
                source = f"{base}.{source}" if source else base
            for alias in statement.names:
                bound[alias.asname or alias.name] = f"{source}.{alias.name}"

    def dotted_name(expr: ast.expr) -> str | None:
        if isinstance(expr, ast.Name):
            return bound.get(expr.id)
        if isinstance(expr, ast.Attribute):
            owner = dotted_name(expr.value)
            return f"{owner}.{expr.attr}" if owner else None
        return None

    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and dotted_name(node.func) == _DEPRECATED
    ]


@pytest.mark.parametrize(
    "source",
    [
        "from hamilton.dev_utils.deprecation import deprecated\ndeprecated()",
        "from hamilton.dev_utils.deprecation import deprecated as old\nold()",
        "from hamilton.dev_utils import deprecation\ndeprecation.deprecated()",
        "import hamilton.dev_utils.deprecation as d\nd.deprecated()",
        "import hamilton.dev_utils.deprecation\nhamilton.dev_utils.deprecation.deprecated()",
        "from hamilton import dev_utils\ndev_utils.deprecation.deprecated()",
        "from ..dev_utils.deprecation import deprecated\ndeprecated()",
        "from ..dev_utils import deprecation\ndeprecation.deprecated()",
        "from .. import dev_utils\ndev_utils.deprecation.deprecated()",
    ],
)
def test_the_lock_finds_deprecated_under_every_import_form(source):
    tree = ast.parse(source)
    assert len(_deprecated_calls(tree, "hamilton.function_modifiers.example")) == 1


def test_no_deprecation_in_hamilton_pins_its_current_version():
    """A pinned current_version freezes a deprecation's clock: it never starts warning, or warns forever
    and never fails. Every deprecation must read the running release instead."""
    package = pathlib.Path(hamilton.__file__).parent
    applications, pinned = 0, []
    for path in sorted(package.rglob("*.py")):
        relative = path.relative_to(package.parent).with_suffix("")
        is_package = relative.name == "__init__"
        module = ".".join(relative.parent.parts if is_package else relative.parts)
        tree = ast.parse(path.read_text(), filename=str(path))
        for call in _deprecated_calls(tree, module, is_package):
            applications += 1
            if len(call.args) > _CURRENT_VERSION_POSITION or any(
                keyword.arg == "current_version" for keyword in call.keywords
            ):
                pinned.append(f"{path.relative_to(package.parent)}:{call.lineno}")
    assert applications, "found no deprecations to check; the scan is broken"
    assert pinned == []


def _decorated_function(**overrides):
    arguments = dict(
        warn_starting=(1, 0, 0),
        fail_starting=(2, 0, 0),
        use_this=None,
        explanation="Use the new one.",
        migration_guide="https://example.com/guide",
        current_version=(1, 5, 0),
    )

    @deprecated(**{**arguments, **overrides})
    def old_api() -> str:
        return "result"

    return old_api


def _decorated_class(**overrides):
    arguments = dict(
        warn_starting=(1, 0, 0),
        fail_starting=(2, 0, 0),
        use_this=None,
        explanation="Use the new one.",
        migration_guide="https://example.com/guide",
        current_version=(1, 5, 0),
    )

    @deprecated(**{**arguments, **overrides})
    class OldDecorator:
        def __call__(self) -> str:
            return "result"

    return OldDecorator()


@pytest.mark.parametrize(
    "decorate", [_decorated_function, _decorated_class], ids=["function", "class"]
)
def test_deprecation_warns_with_a_future_warning_at_the_calling_line(decorate):
    old_api = decorate()
    with pytest.warns(FutureWarning, match="2.0.0") as record:
        calling_line = inspect.currentframe().f_lineno + 1
        assert old_api() == "result"
    assert len(record) == 1
    assert (record[0].filename, record[0].lineno) == (__file__, calling_line)


@pytest.mark.parametrize(
    "decorate", [_decorated_function, _decorated_class], ids=["function", "class"]
)
def test_deprecation_warning_follows_the_warning_filters(decorate):
    old_api = decorate()
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        with pytest.raises(FutureWarning):
            old_api()
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("ignore", FutureWarning)
        assert old_api() == "result"
    assert record == []


@pytest.mark.parametrize(
    "decorate", [_decorated_function, _decorated_class], ids=["function", "class"]
)
def test_custom_warn_action_replaces_the_warning(decorate):
    messages = []
    old_api = decorate(warn_action=messages.append)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert old_api() == "result"
    assert len(messages) == 1


class _LinearCombination(models.BaseModel):
    def get_dependents(self) -> list[str]:
        return list(self.config_parameters.keys())

    def predict(self, **columns: pd.Series) -> pd.Series:
        return sum(self.config_parameters[name] * column for name, column in columns.items())


def _apply(decorator_cls: type) -> int:
    """Applies the decorator as a user's module does; returns the line that applies it."""

    def my_column() -> pd.Series:
        pass

    applying_line = inspect.currentframe().f_lineno + 1
    decorator_cls(_LinearCombination, "my_column_model_params")(my_column)
    return applying_line


@pytest.mark.parametrize("decorator_cls", [macros.dynamic_transform, macros.model])
def test_dynamic_transform_and_model_warn_once_under_their_own_names(decorator_cls):
    with pytest.warns(FutureWarning) as record:
        applying_line = _apply(decorator_cls)
    assert [str(warning.message).split(" ")[0] for warning in record] == [
        decorator_cls.__qualname__
    ]
    assert (record[0].filename, record[0].lineno) == (__file__, applying_line)


@pytest.mark.parametrize("version", [(2, 0, 0), (2, 1, 0)], ids=["2.0.0", "2.1.0"])
@pytest.mark.parametrize("decorator_cls", [macros.dynamic_transform, macros.model, macros.pipe])
def test_class_deprecations_fail_on_2_x_under_their_own_names(decorator_cls, version, monkeypatch):
    for cls in decorator_cls.__mro__:
        deprecator = getattr(vars(cls).get("__call__"), deprecation._DEPRECATION_ATTR, None)
        if deprecator is not None:
            monkeypatch.setattr(deprecator, "current_version", Version(*version))
    with pytest.raises(
        DeprecationError, match=f"^{decorator_cls.__qualname__} has been deprecated"
    ):
        if decorator_cls is macros.pipe:
            decorator_cls()(lambda: None)
        else:
            _apply(decorator_cls)


def _deprecate_class(messages: list[str]):
    return deprecated(
        warn_starting=(1, 0, 0),
        fail_starting=(2, 0, 0),
        use_this=None,
        explanation="Use the new one.",
        migration_guide="https://example.com/guide",
        current_version=(1, 5, 0),
        warn_action=messages.append,
    )


def test_plain_subclass_of_a_deprecated_class_warns_once_under_its_parents_name():
    messages = []

    @_deprecate_class(messages)
    class Parent:
        def __call__(self) -> str:
            return "result"

    class Child(Parent):
        pass

    class ChildCallingSuper(Parent):
        def __call__(self) -> str:
            return super().__call__()

    assert Child()() == "result"
    assert ChildCallingSuper()() == "result"
    assert [message.split(" ")[0] for message in messages] == [Parent.__qualname__] * 2


@pytest.mark.parametrize("calls_super", [False, True], ids=["inherits-call", "overrides-call"])
def test_deprecated_subclass_of_a_deprecated_class_warns_once_under_its_own_name(calls_super):
    messages = []

    @_deprecate_class(messages)
    class Parent:
        def __call__(self) -> str:
            return "result"

    if calls_super:

        @_deprecate_class(messages)
        class Child(Parent):
            def __call__(self) -> str:
                return super().__call__()

    else:

        @_deprecate_class(messages)
        class Child(Parent):
            pass

    assert Child()() == "result"
    assert [message.split(" ")[0] for message in messages] == [Child.__qualname__]
