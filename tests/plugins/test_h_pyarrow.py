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

import pandas as pd
import pyarrow
import pytest

from hamilton.plugins import h_pyarrow


@pytest.fixture()
def pandas():
    return pd.DataFrame({"a": [0, 1, 2], "b": ["a", "b", "c"]})


def test_pandas_to_pyarrow(pandas):
    result_builder = h_pyarrow.PyarrowTableResult()
    data = {"df": pandas}
    # ResultBuilder receive unpacked dict as arg, i.e., kwargs only
    table = result_builder.build_result(**data)
    assert isinstance(table, pyarrow.Table)


def test_fail_for_multiple_outputs(pandas):
    result_builder = h_pyarrow.PyarrowTableResult()
    data = {"df": pandas, "df2": pandas}
    with pytest.raises(AssertionError):
        result_builder.build_result(**data)
