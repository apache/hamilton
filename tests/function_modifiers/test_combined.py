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

"""A few tests for combining different decorators.
While this should not be necessary -- we should be able to test the decorator lifecycle functions,
it is useful to have a few tests that demonstrate that common use-cases are supported.

Note we also have some more end-to-end cases in test_layered.py"""

from typing import Dict

import pandas as pd

from hamilton.function_modifiers import base as fm_base
from hamilton.function_modifiers import extract_columns, extract_fields, subdag, tag


def test_subdag_and_extract_columns():
    def foo() -> pd.Series:
        return pd.Series([1, 2, 3])

    def bar() -> pd.Series:
        return pd.Series([1, 2, 3])

    @extract_columns("foo", "bar")
    @subdag(foo, bar)
    def foo_bar(foo: pd.Series, bar: pd.Series) -> pd.DataFrame:
        return pd.DataFrame({"foo": foo, "bar": bar})

    nodes = fm_base.resolve_nodes(foo_bar, {})
    nodes_by_name = {node.name: node for node in nodes}
    assert sorted(nodes_by_name) == ["bar", "foo", "foo_bar", "foo_bar.bar", "foo_bar.foo"]
    # The extraction columns should depend on the thing from which they are extracted
    assert sorted(nodes_by_name["foo"].input_types.keys()) == ["foo_bar"]
    assert sorted(nodes_by_name["bar"].input_types.keys()) == ["foo_bar"]


def test_subdag_and_extract_fields():
    def foo() -> int:
        return 1

    def bar() -> int:
        return 2

    @extract_fields({"foo": int, "bar": int})
    @subdag(foo, bar)
    def foo_bar(foo: int, bar: pd.Series) -> Dict[str, int]:
        return {"foo": foo, "bar": bar}

    nodes = fm_base.resolve_nodes(foo_bar, {})
    nodes_by_name = {node.name: node for node in nodes}
    assert sorted(nodes_by_name) == ["bar", "foo", "foo_bar", "foo_bar.bar", "foo_bar.foo"]
    # The extraction columns should depend on the thing from which they are extracted
    assert sorted(nodes_by_name["foo"].input_types.keys()) == ["foo_bar"]
    assert sorted(nodes_by_name["bar"].input_types.keys()) == ["foo_bar"]


def test_subdag_and_extract_fields_with_tags():
    def foo() -> int:
        return 1

    def bar() -> int:
        return 2

    @tag(a="b", target_="foo")
    @tag(a="c", target_="bar")
    @extract_fields({"foo": int, "bar": int})
    @subdag(foo, bar)
    def foo_bar(foo: int, bar: pd.Series) -> Dict[str, int]:
        return {"foo": foo, "bar": bar}

    nodes = fm_base.resolve_nodes(foo_bar, {})
    nodes_by_name = {node.name: node for node in nodes}
    assert sorted(nodes_by_name) == ["bar", "foo", "foo_bar", "foo_bar.bar", "foo_bar.foo"]
    # The extraction columns should depend on the thing from which they are extracted
    assert sorted(nodes_by_name["foo"].input_types.keys()) == ["foo_bar"]
    assert sorted(nodes_by_name["bar"].input_types.keys()) == ["foo_bar"]
    assert nodes_by_name["foo"].tags["a"] == "b"
    assert nodes_by_name["bar"].tags["a"] == "c"


def test_subdag_and_extract_fields_dangling_nodes():
    def foo() -> int:
        return 1

    def bar() -> int:
        return 2

    @extract_fields({"foo": int, "bar": int})
    @subdag(foo, bar)
    def foo_bar(foo: int) -> Dict[str, int]:
        return {"foo": foo, "bar": 5}

    nodes = fm_base.resolve_nodes(foo_bar, {})
    nodes_by_name = {node.name: node for node in nodes}
    # Doing this set comparison as I'm not sure that foo_bar.bar should actually be in there
    assert len({"bar", "foo", "foo_bar", "foo_bar.foo"} - set(nodes_by_name)) == 0
    # The extraction columns should depend on the thing from which they are extracted
    assert sorted(nodes_by_name["foo"].input_types.keys()) == ["foo_bar"]
    assert sorted(nodes_by_name["bar"].input_types.keys()) == ["foo_bar"]
