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
from pandas.core.groupby import DataFrameGroupBy

from hamilton.function_modifiers import parameterize_values, tag


@tag(stage="production")
@parameterize_values(
    parameter="n",
    assigned_output={
        ("lag_sales_1", ""): 1,
        ("lag_sales_2", ""): 2,
        ("lag_sales_3", ""): 3,
        ("lag_sales_4", ""): 4,
        ("lag_sales_5", ""): 5,
        ("lag_sales_6", ""): 6,
        ("lag_sales_7", ""): 7,
        ("lag_sales_29", ""): 29,
        ("lag_sales_30", ""): 30,
    },
)
def lag_sales_n(grp_date_store_item: DataFrameGroupBy, output_idx: pd.Index, n: int) -> pd.Series:
    df = grp_date_store_item.shift(n)
    return df.loc[output_idx]["sales"].dropna()
