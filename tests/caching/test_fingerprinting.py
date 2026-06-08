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

"""Due to the recursive nature of hashing of sequences, mappings, and other
complex types, many tests are not "true" unit tests. The base cases are
the original `hash_value()` and the `hash_primitive()` functions.
"""

import numpy as np
import pandas as pd
import pytest

from hamilton.caching import fingerprinting


def test_hash_none():
    fingerprint = fingerprinting.hash_value(None)
    assert fingerprint == "<none>"


def test_hash_no_dict_attribute():
    """Classes without a __dict__ attribute can't be hashed.
    during the base case.
    """

    class Foo:
        __slots__ = ()

    obj = Foo()
    assert not hasattr(obj, "__dict__")

    fingerprint = fingerprinting.hash_value(obj)

    assert fingerprint == fingerprinting.UNHASHABLE


def test_empty_dict_attr_is_unhashable():
    """Classes with an empty __dict__ can't be hashed during the base case."""

    class Foo: ...  # noqa: E701

    obj = Foo()
    assert obj.__dict__ == {}

    fingerprint = fingerprinting.hash_value(obj)

    assert fingerprint == fingerprinting.UNHASHABLE


def test_hash_recursively():
    """Classes without a specialized hash function are hashed recursively
    via their __dict__ attribute.
    """

    class Foo:
        def __init__(self, obj):
            self.foo = "foo"
            self.obj = obj

    foo0 = Foo(obj=None)
    foo1 = Foo(obj=foo0)
    foo2 = Foo(obj=foo1)

    foo0_dict = {"foo": "foo", "obj": None}
    foo1_dict = {"foo": "foo", "obj": foo0_dict}
    foo2_dict = {"foo": "foo", "obj": foo1_dict}

    assert foo0.__dict__ == foo0_dict
    # NOTE foo2.__dict__ != foo2_dict, because foo2.__dict__ holds
    # a reference to the object foo1, which is not the case for foo2_dict

    fingerprint0 = fingerprinting.hash_value(foo0)
    assert fingerprint0 == fingerprinting.hash_value(foo0_dict)

    fingerprint1 = fingerprinting.hash_value(foo1)
    assert fingerprint1 == fingerprinting.hash_value(foo1_dict)

    fingerprint2 = fingerprinting.hash_value(foo2)
    assert fingerprint2 == fingerprinting.hash_value(foo2_dict)


def test_max_recursion_depth():
    """Set the max recursion depth to 0 to prevent any recursion.
    After max depth, the default case should return UNHASHABLE.
    """

    class Foo:
        def __init__(self, obj):
            self.foo = "foo"
            self.obj = obj

    foo0 = Foo(obj=None)
    foo1 = Foo(obj=foo0)
    foo2 = Foo(obj=foo1)

    foo0_dict = {"foo": "foo", "obj": None}
    assert foo0.__dict__ == foo0_dict

    fingerprint0 = fingerprinting.hash_value(foo0)
    assert fingerprint0 == fingerprinting.hash_value(foo0_dict)

    fingerprinting.set_max_depth(1)
    # equivalent after reaching max depth
    fingerprint1 = fingerprinting.hash_value(foo1)
    fingerprint2 = fingerprinting.hash_value(foo2)
    assert fingerprint1 == fingerprint2

    fingerprinting.set_max_depth(2)
    # no longer equivalent after increasing max depth
    fingerprint1 = fingerprinting.hash_value(foo1)
    fingerprint2 = fingerprinting.hash_value(foo2)
    assert fingerprint1 != fingerprint2


# ---------------------------------------------------------------------------
# Portability / algorithm-stability guard
#
# The tests below pin literal digests. They cover only types that hash
# deterministically across platforms and library versions: their digest is a
# function of the value's Python representation (or, for numpy, an explicit
# shape + dtype + raw bytes) and the hashing algorithm alone. Pinning them
# guards against an accidental change to the hashing algorithm and documents
# that the fingerprint is reproducible on other machines.
#
# Version-sensitive types (pandas / polars DataFrames, whose digest depends on
# library-version-specific dtype reprs and row-hash internals) are NOT pinned
# here; they are covered by the relational must-differ / must-match tests
# further down, which assert behavior rather than an exact digest.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("obj", "expected_hash"),
    [
        ("hello-world", "L1Q1Kh6_t1atHO_H8RbBeA=="),
        (17.31231, "mJPTpPyXDSZgU-u8NuztIQ=="),
        (16474, "6MgAp1NbMW0ZZpe_8iKVsg=="),
        (True, "J2eGynSuIpd5bwVQzO9VVg=="),
        (b"\x951!\x89u=\xe6\xadG\xdf", "d1DufDgRQmqi9Kt4Z2PeUQ=="),
    ],
)
def test_hash_primitive(obj, expected_hash):
    fingerprint = fingerprinting.hash_primitive(obj)
    assert fingerprint == expected_hash


@pytest.mark.parametrize(
    ("obj", "expected_hash"),
    [
        ([0, True, "hello-world"], "mlOjj4yeCrSDFSn5zgdEIg=="),
        ((17.0, False, "world"), "BcRSGfyKeIOdym9B6TmAyQ=="),
    ],
)
def test_hash_sequence(obj, expected_hash):
    fingerprint = fingerprinting.hash_sequence(obj)
    assert fingerprint == expected_hash


def test_hash_equals_for_different_sequence_types():
    list_obj = [0, True, "hello-world"]
    tuple_obj = (0, True, "hello-world")
    expected_hash = "mlOjj4yeCrSDFSn5zgdEIg=="

    list_fingerprint = fingerprinting.hash_sequence(list_obj)
    tuple_fingerprint = fingerprinting.hash_sequence(tuple_obj)
    assert list_fingerprint == tuple_fingerprint == expected_hash


def test_hash_ordered_mapping():
    obj = {0: True, "key": "value", 17.0: None}
    expected_hash = "GyxyI9-pq-EJJvSAIN509g=="
    fingerprint = fingerprinting.hash_mapping(obj, ignore_order=False)
    assert fingerprint == expected_hash


def test_hash_mapping_where_order_matters():
    obj1 = {0: True, "key": "value", 17.0: None}
    obj2 = {"key": "value", 17.0: None, 0: True}
    fingerprint1 = fingerprinting.hash_mapping(obj1, ignore_order=False)
    fingerprint2 = fingerprinting.hash_mapping(obj2, ignore_order=False)
    assert fingerprint1 != fingerprint2


def test_hash_unordered_mapping():
    obj = {0: True, "key": "value", 17.0: None}
    expected_hash = "cDuuL2eA3DaSWlWW3u7o9g=="
    fingerprint = fingerprinting.hash_mapping(obj, ignore_order=True)
    assert fingerprint == expected_hash


def test_hash_mapping_where_order_doesnt_matter():
    obj1 = {0: True, "key": "value", 17.0: None}
    obj2 = {"key": "value", 17.0: None, 0: True}
    fingerprint1 = fingerprinting.hash_mapping(obj1, ignore_order=True)
    fingerprint2 = fingerprinting.hash_mapping(obj2, ignore_order=True)
    assert fingerprint1 == fingerprint2


def test_hash_set():
    obj = {0, True, "key", "value", 17.0, None}
    expected_hash = "E_f_tjbi6qn7KL3NUCZayg=="
    fingerprint = fingerprinting.hash_set(obj)
    assert fingerprint == expected_hash


def test_hash_numpy():
    # dtype is pinned explicitly so the literal digest is reproducible across
    # platforms (the default integer dtype is platform-dependent).
    array = np.array([[0, 1], [2, 3]], dtype=np.int64)
    expected_hash = "024zwZIcWy6r4dlX4AMTow=="
    fingerprint = fingerprinting.hash_value(array)
    assert fingerprint == expected_hash


def test_hash_numpy_different_shapes_differ():
    """Arrays with the same raw bytes but different shapes must hash differently."""
    a = np.array([1, 2, 3, 4, 5, 6])
    b = np.array([[1, 2, 3], [4, 5, 6]])
    assert fingerprinting.hash_value(a) != fingerprinting.hash_value(b)


def test_hash_numpy_different_dtypes_differ():
    """Arrays with the same bit pattern but different dtypes must hash differently."""
    a = np.array([1.0], dtype=np.float32)
    b = np.array([1065353216], dtype=np.int32)  # same 4 bytes as float32(1.0)
    assert a.tobytes() == b.tobytes()  # confirm same raw bytes
    assert fingerprinting.hash_value(a) != fingerprinting.hash_value(b)


def test_hash_pandas_same_data_matches():
    """Identical pandas DataFrames must produce the same hash (determinism)."""
    a = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    b = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    assert fingerprinting.hash_value(a) == fingerprinting.hash_value(b)


def test_hash_polars_different_columns_differ():
    """DataFrames with identical values but different column names must hash differently."""
    polars = pytest.importorskip("polars")
    a = polars.DataFrame({"region": ["East", "West"], "revenue": [100, 200]})
    b = polars.DataFrame({"student": ["East", "West"], "height_cm": [100, 200]})
    assert fingerprinting.hash_value(a) != fingerprinting.hash_value(b)


def test_hash_polars_same_schema_same_data_matches():
    """Identical DataFrames must produce the same hash."""
    polars = pytest.importorskip("polars")
    a = polars.DataFrame({"x": [1, 2], "y": [3, 4]})
    b = polars.DataFrame({"x": [1, 2], "y": [3, 4]})
    assert fingerprinting.hash_value(a) == fingerprinting.hash_value(b)


def test_hash_cross_type_primitives_differ():
    """Values with the same string form but different types must hash differently.

    Before type tagging, ``str(1) == str("1") == "1"`` collapsed int/str (and
    likewise float/str and bytes/str) into identical fingerprints.
    """
    fingerprints = {
        fingerprinting.hash_value(1),
        fingerprinting.hash_value("1"),
        fingerprinting.hash_value(b"1"),
        fingerprinting.hash_value(1.0),
        fingerprinting.hash_value("1.0"),
    }
    assert len(fingerprints) == 5
