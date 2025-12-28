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


def df() -> pd.DataFrame:
    """Create a pandas dataframe"""
    return pd.DataFrame(
        {
            "a": [0, 1, 2, 3],
            "b": [True, False, False, False],
            "c": ["ok", "hello", "no", "world"],
        }
    )


def df_with_new_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Adding columns"""
    df["x"] = [1.0, 2.0, 3.0, -1]
    df["y"] = None
    return df


def df_with_renamed_cols(df_with_new_cols: pd.DataFrame) -> pd.DataFrame:
    return df_with_new_cols.rename(columns={"a": "aa", "b": "B"})


if __name__ == "__main__":
    import json

    import __main__
    from hamilton import driver
    from hamilton.plugins import h_schema

    validator_adapter = h_schema.SchemaValidator("./schemas")
    dr = driver.Builder().with_modules(__main__).with_adapters(validator_adapter).build()
    res = dr.execute(["df_with_renamed_cols"])
    print(json.dumps(validator_adapter.json_schemas, indent=2))
