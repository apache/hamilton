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

"""Pyspark UDFs

Has to only contain map operations!

Notes:

1. Hamilton will first try to satisfy running these UDFs with columns from the dataframe, else it will take from the
input dictionary that are not part of the pyspark dataframe.
2. UDFs defined this way operate in a row-by-row fashion, so they are not vectorized.

"""


def spend_per_signup(spend: float, signups: float) -> float:
    """The cost per signup in relation to spend."""
    return spend / signups


def augmented_mean(foo: float, bar: float) -> float:
    """Shows you can include functions that don't depend on columns in the dataframe if you want to do
    other things with Hamilton at the same time as computing. If Hamilton does not find a match in the
    dataframe it'll look for a match in the inputs dictionary."""
    return foo + bar


def spend_zero_mean(spend: float, spend_mean: float) -> float:
    """Computes zero mean spend.
    Note:
        `spend_mean` here COULD come from the dataframe OR the input dictionary.
    """
    return spend - spend_mean


def spend_zero_mean_unit_variance(spend_zero_mean: float, spend_std_dev: float) -> float:
    """Function showing one way to make spend have zero mean and unit variance.
    Note:
        `spend_std_dev` here COULD come from the pyspark dataframe OR the input dictionary.
    """
    return spend_zero_mean / spend_std_dev
