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

import pytest

from hamilton.function_modifiers import InvalidDecoratorException, source, value
from hamilton.function_modifiers.dependencies import (
    LiteralDependency,
    UpstreamDependency,
    _validate_group_params,
)


@pytest.mark.parametrize(
    "upstream_source,expected",
    [("foo", UpstreamDependency("foo")), (UpstreamDependency("bar"), UpstreamDependency("bar"))],
)
def test_upstream(upstream_source, expected):
    assert source(upstream_source) == expected


@pytest.mark.parametrize(
    "literal_value,expected",
    [
        ("foo", LiteralDependency("foo")),
        (LiteralDependency("foo"), LiteralDependency("foo")),
        (1, LiteralDependency(1)),
    ],
)
def test_literal(literal_value, expected):
    assert value(literal_value) == expected


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ([source("foo"), source("bar")], {}),
        ([source("foo"), value("bar")], {}),
        ([], {"foo": source("foo"), "bar": source("bar")}),
        ([value("foo"), value("bar")], {}),
        ([], {"foo": value("foo"), "bar": value("bar")}),
        ([], {"foo": value("foo"), "bar": source("bar")}),
    ],
)
def test_validate_group_happy(args, kwargs):
    """Tests valid calls to group(...) have no error"""
    _validate_group_params(args, kwargs)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ([source("foo"), source("bar")], {"foo": source("foo")}),
        ([source("foo"), value("bar")], {"foo": source("foo")}),
        ([], {"foo": "foo", "bar": source("bar")}),
        (["bar"], {}),
        ({}, {}),
    ],
)
def test_validate_group_sad(args, kwargs):
    """Tests invalid calls to group(...) error out"""
    with pytest.raises(InvalidDecoratorException):
        _validate_group_params(args, kwargs)
