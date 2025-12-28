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

import duckdb
import ibis
import ibis.expr.types as ir
import pandas as pd
import pyarrow

from hamilton.function_modifiers import config


def pyarrow_table() -> pyarrow.Table:
    """Create a duckdb table in-memory and return it as a PyArrow table"""
    con = duckdb.connect(database=":memory:")
    con.execute("CREATE TABLE items (item VARCHAR, value DECIMAL(10, 2), count INTEGER)")
    con.execute("INSERT INTO items VALUES ('jeans', 20.0, 1), ('hammer', 42.2, 2)")
    return con.execute("SELECT * FROM items").fetch_arrow_table()


def ibis_rename(pyarrow_table: pyarrow.Table) -> ir.Table:
    """Rename the columns"""
    table = ibis.memtable(pyarrow_table)
    return table.rename(object="item", price="value", number="count")


@config.when(version="1")
def pandas_new_col__v1(ibis_rename: ir.Table) -> pd.DataFrame:
    """Add the column `new_col`"""
    df = ibis_rename.to_pandas()
    df["col_a"] = True
    return df


@config.when(version="2")
def pandas_new_col__v2(ibis_rename: ir.Table) -> pd.DataFrame:
    """Add the columns `new_col` and `another_col`"""
    df = ibis_rename.to_pandas()
    df["col_a"] = True
    df["col_b"] = "X"
    return df


@config.when(version="3")
def pandas_new_col__v4(ibis_rename: ir.Table) -> pd.DataFrame:
    """Add the column `new_col` of type float"""
    df = ibis_rename.to_pandas()
    df["col_a"] = 1.0
    return df


if __name__ == "__main__":
    import argparse
    import json

    import __main__
    from hamilton import driver
    from hamilton.plugins import h_schema

    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="1", type=str, help="The Driver config version")
    parser.add_argument(
        "--no-check", action="store_false", help="Disable `check` to update the stored schemas."
    )
    args = parser.parse_args()
    validator_adapter = h_schema.SchemaValidator(
        "./multi_schemas", check=args.no_check, importance="warn"
    )
    dr = (
        driver.Builder()
        .with_modules(__main__)
        .with_config(dict(version=args.version))
        .with_adapters(validator_adapter)
        .build()
    )
    res = dr.execute(["pandas_new_col"])
    print(res["pandas_new_col"].head())
    print()

    print(json.dumps(validator_adapter.json_schemas, indent=2))
