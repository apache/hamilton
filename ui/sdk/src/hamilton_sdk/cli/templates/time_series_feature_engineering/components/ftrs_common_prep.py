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
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from hamilton.function_modifiers import extract_columns, tag


def output_idx(lag_sales_31: pd.Series) -> pd.Index:
    return lag_sales_31.index


def grp_date_store_item(sales_data_set: DataFrame) -> DataFrameGroupBy:
    return sales_data_set.groupby(by=["store", "item"])


@tag(stage="production")
def lag_sales_31(grp_date_store_item: DataFrameGroupBy) -> pd.Series:
    df = grp_date_store_item.shift(31)
    res = df["sales"].dropna()
    return res


@tag(stage="production")
@extract_columns("store", "item", "sales")
def sales_data_columns(sales_data_set_output_idx: pd.DataFrame) -> pd.DataFrame:
    return sales_data_set_output_idx
