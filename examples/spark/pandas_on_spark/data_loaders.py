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
import pyspark.pandas as ps

from hamilton.function_modifiers import extract_columns

# You could have two separate loaders:
#
# def spend(spend_location: str) -> ps.Series:
#     """Dummy function showing how to wire through loading data.
#
#     :param spend_location:
#     :return:
#     """
#     return ps.from_pandas(pd.Series([10, 10, 20, 40, 40, 50], name="spend"))
#
#
# def signups(signups_location: str) -> ps.Series:
#     """Dummy function showing how to wire through loading data.
#
#     :param signups_location:
#     :return:
#     """
#     return ps.from_pandas(pd.Series([1, 10, 50, 100, 200, 400], name="signups"))


# Or one loader where you extract its columns:
@extract_columns("spend", "signups")
def base_df(base_df_location: str) -> ps.DataFrame:
    """Dummy function showing how to wire through loading data.

    :param location:
    :return:
    """
    return ps.from_pandas(
        pd.DataFrame({"spend": [10, 10, 20, 40, 40, 50], "signups": [1, 10, 50, 100, 200, 400]})
    )
