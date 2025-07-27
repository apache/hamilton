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

from typing import Any, Type

import pyarrow
from pyarrow.interchange import from_dataframe

from hamilton.lifecycle.api import ResultBuilder


class PyarrowTableResult(ResultBuilder):
    """Add this result builder to a materializer's `combine` statement to convert your dataframe
    object to a pyarrow representation and make it compatible with pyarrow DataSavers.

    It implicitly support input_type == Any, but it expects dataframe objects implementing
    the dataframe interchange protocol: ref: https://arrow.apache.org/docs/python/interchange_protocol.html
    for example:
    - pandas
    - polars
    - dask
    - vaex
    - ibis
    - duckdb results
    """

    def output_type(self) -> Type:
        return pyarrow.Table

    def build_result(self, **outputs: Any) -> Any:
        """This function converts objects implementing the `__dataframe__` protocol to
        a pyarrow table. It doesn't support receiving multiple outputs because it can't
        handle any joining logic.

        ref: https://arrow.apache.org/docs/python/interchange_protocol.html
        """
        if len(outputs) != 1:
            raise AssertionError(
                "PyarrowTableResult can only receive 1 output, i.e., only one item in `to.SAVER(dependencies=[])`"
                f"It received {len(outputs)} outputs."
            )
        return from_dataframe(next(iter(outputs.values())))
