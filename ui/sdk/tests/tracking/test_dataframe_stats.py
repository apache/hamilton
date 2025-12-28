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

import math

import numpy as np
import pandas as pd
from hamilton_sdk.tracking import dataframe_stats
from pytest import mark, param


skip_NAN_on_numpy_v2 = mark.skipif(
    not hasattr(np, "NAN"),
    reason="NAN is not available in numpy v2",
)


# Tests the type converter
@mark.parametrize(
    "input, expected",
    [
        (1, 1),
        ("1", "1"),
        (1.0, 1.0),
        (True, True),
        (False, False),
        (None, None),
        (np.array([1, 2, 3]), [1, 2, 3]),
        ({"a": 1, "b": 2}, {"a": 1, "b": 2}),
        ({"a": 1, "b": 2, "c": {"d": np.int8(3), "e": 4}}, {"a": 1, "b": 2, "c": {"d": 3, "e": 4}}),
        (pd.NaT, None),
        (pd.NA, None),
        param(getattr(np, "NAN", np.nan), None, marks=skip_NAN_on_numpy_v2),
        (np.nan, None),
        (math.nan, None),
        # (math.inf, None),
    ]
    + [(f(1), 1) for f in [np.int8, np.uint8, np.int32, np.int64]]
    + [(f(1.0), 1.0) for f in [np.float16, np.float32, np.float64]]
    + [(f(1.0 + 1.0j), 1.0 + 1.0j) for f in [np.complex64, np.complex128]],
)
def test_type_converter(input, expected):
    actual = dataframe_stats.type_converter(input)
    assert actual == expected
