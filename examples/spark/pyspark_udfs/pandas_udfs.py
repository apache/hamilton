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

"""Pandas UDFs.

Has to only contain map operations! Aggregations, filters, etc. are not supported.

Notes:

1. Functions that are annotated with pd.Series for all inputs and output, will be converted to pandas UDFs.
Note - we could broaden support for more function type signatures, but this is a good start. Please make an
issue/discussion if this is something you'd like to see.
2. You need to use the `h_typing.column` annotation for the output type. This is because we need to know what
underlying primitive type the pandas series is. This is a limitation of the pandas UDFs on pyspark.
3. If a function is deemed to be a pandas_udf one, Hamilton will try to satisfy running these UDFs with columns from
the dataframe ONLY. This is different from how the vanilla UDFs behave. This is partially a limitation of pandas UDFs.
4. Pandas_udfs operate over chunks of data, and can thus operate in a vectorized manner. This is a big performance gain
over vanilla UDFs.
5. You can have non-pandas_udf functions in the same file, and will be run as row based UDFs.

"""

import pandas as pd

from hamilton.htypes import column


def spend_per_signup(spend: pd.Series, signups: pd.Series) -> column[pd.Series, float]:
    """The cost per signup in relation to spend."""
    return spend / signups


def augmented_mean(foo: float, bar: float) -> float:
    """Shows you can include functions that don't depend on columns in the dataframe if you want to do
    other things with Hamilton at the same time as computing. If Hamilton does not find a match in the
    dataframe it'll look for a match in the inputs dictionary.
    """
    return foo + bar


def spend_zero_mean(spend: pd.Series, spend_mean: pd.Series) -> column[pd.Series, float]:
    """Computes zero mean spend.
    Note:
        `spend_mean` here HAS TO come from the dataframe or the input dictionary.
    """
    return spend - spend_mean


def spend_zero_mean_unit_variance(
    spend_zero_mean: pd.Series, spend_std_dev: pd.Series
) -> column[pd.Series, float]:
    """Function showing one way to make spend have zero mean and unit variance.
    Note:
        `spend_std_dev` here HAS TO come from the pyspark dataframe.
    """
    return spend_zero_mean / spend_std_dev
