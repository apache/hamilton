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

import enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, RootModel


class Describe(enum.Enum):
    project = "project"


class Attribute(BaseModel):
    _describes: Describe
    _version: int


class Attribute__documentation_loom__1(Attribute):
    _describes: Describe = "project"
    _version: int = 1
    id: str


class Attribute__dagworks_describe__2(Attribute):
    _describes: Describe = "node"
    _version: int = 2


class DWDescribeV003_BaseColumnStatistics(BaseModel):
    name: str
    pos: int
    data_type: str
    count: int
    missing: int
    base_data_type: str


class DWDescribeV003_UnhandledColumnStatistics(DWDescribeV003_BaseColumnStatistics):
    pass


class DWDescribeV003_BooleanColumnStatistics(DWDescribeV003_BaseColumnStatistics):
    zeros: int


class DWDescribeV003_NumericColumnStatistics(DWDescribeV003_BaseColumnStatistics):
    zeros: int
    min: float
    max: float
    mean: float
    std: float
    quantiles: Dict[float, float]
    histogram: Dict[str, int]


class DWDescribeV003_DatetimeColumnStatistics(DWDescribeV003_BaseColumnStatistics):
    pass


class DWDescribeV003_CategoryColumnStatistics(DWDescribeV003_BaseColumnStatistics):
    empty: int
    domain: Dict[str, int]
    top_value: str
    top_freq: int
    unique: int


class DWDescribeV003_StringColumnStatistics(DWDescribeV003_BaseColumnStatistics):
    avg_str_len: float
    std_str_len: float
    empty: int


class Attribute__dagworks_describe__3(
    RootModel[
        Dict[
            str,
            Union[
                DWDescribeV003_UnhandledColumnStatistics,
                DWDescribeV003_BooleanColumnStatistics,
                DWDescribeV003_NumericColumnStatistics,
                DWDescribeV003_DatetimeColumnStatistics,
                DWDescribeV003_CategoryColumnStatistics,
                DWDescribeV003_StringColumnStatistics,
            ],
        ]
    ]
):
    _describes: Describe = "node"
    _version: int = 3

    class Config:
        arbitrary_types_allowed = "allow"


class Attribute__dict__1(Attribute):
    _describes: Describe = "node"
    _version: int = 1
    type: str
    value: str


class Attribute__dict__2(Attribute):
    _describes: Describe = "node"
    _version: int = 2
    type: str
    value: dict


class Attribute__error__1(Attribute):
    _describes: Describe = "node"
    _version: int = 1
    stack_trace: List[str]


class PandasDescribeNumericColumn(BaseModel):
    count: int
    mean: float
    min: float
    max: float
    std: float
    q_25_percent: float = Field(..., alias="25%")
    q_50_percent: float = Field(..., alias="50%")
    q_75_percent: float = Field(..., alias="75%")
    dtype: str


class PandasDescribeCategoricalColumn(BaseModel):
    count: Optional[int]
    unique: int
    top: Any
    freq: Optional[int]


class Attribute__pandas_describe__1(
    RootModel[Dict[str, Union[PandasDescribeNumericColumn, PandasDescribeCategoricalColumn]]]
):
    _describes: Describe = "node"
    _version: int = 1


class Attribute__primitive__1(Attribute):
    _describes: Describe = "node"
    _version: int = 1
    type: str
    value: str

    class Config:
        arbitrary_types_allowed = True


class Attribute__unsupported__1(Attribute):
    _describes: Describe = "node"
    _version: int = 1
    action: Optional[str] = None
    unsupported_type: Optional[str] = None
