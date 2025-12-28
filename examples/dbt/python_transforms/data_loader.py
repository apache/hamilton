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

"""
This module contains our data loading functions.
"""

from typing import List

import pandas as pd
import pandera as pa
from sklearn import datasets
from sqlalchemy import engine

from hamilton.function_modifiers import check_output, config, extract_columns


def _sanitize_columns(df_columns: List[str]) -> List[str]:
    """Renames columns to be valid hamilton names -- and lower cases them.
    :param df_columns: the current column names.
    :return: sanitize column names that work with Hamilton
    """
    return [
        c.strip().replace(".", "_").replace("/", "_per_").replace(" ", "_").lower()
        for c in df_columns
    ]


# schema to validate against
passengers_df_schema = pa.DataFrameSchema(
    {
        "pclass": pa.Column(float, nullable=False),
        "sex": pa.Column(str, nullable=False),
        "age": pa.Column(float, nullable=True),
        "parch": pa.Column(float, nullable=False),
        "sibsp": pa.Column(float, nullable=False),
        "fare": pa.Column(float, nullable=True),
        "embarked": pa.Column(str, nullable=True),
        "name": pa.Column(str, nullable=False),
        "ticket": pa.Column(str, nullable=False),
        "boat": pa.Column(str, nullable=True),
        "body": pa.Column(float, nullable=True),
        "home_dest": pa.Column(str, nullable=True),
        "cabin": pa.Column(str, nullable=True),
        "survived": pa.Column(int, nullable=False),
    },
    strict=True,
    index=pa.Index(int, name="pid"),
)


@config.when(loader="sqllite")
def raw_passengers_df__sqllite(connection: engine.Connection) -> pd.DataFrame:
    """Pulls from the SQLlite DB. Becomes a node only if `sqllite` is specified.

    :param connection: the sqllite connection object to use.
    :return: dataframe of data.
    """
    query = """
                SELECT
                    tbl_passengers.pid,
                    tbl_passengers.pclass,
                    tbl_passengers.sex,
                    tbl_passengers.age,
                    tbl_passengers.parch,
                    tbl_passengers.sibsp,
                    tbl_passengers.fare,
                    tbl_passengers.embarked,
                    tbl_passengers.name,
                    tbl_passengers.ticket,
                    tbl_passengers.boat,
                    tbl_passengers.body,
                    tbl_passengers.home_dest,
                    tbl_passengers.cabin,
                    tbl_targets.is_survived as is_survived
                FROM
                    tbl_passengers
                JOIN
                    tbl_targets
                ON
                    tbl_passengers.pid=tbl_targets.pid
            """
    df = pd.read_sql(query, con=connection)
    df.pid = df.pid.astype(int)
    return df


@config.when(loader="openml")
def raw_passengers_df__openml() -> pd.DataFrame:
    """Pulls data from the web. Only becomes a node in the DAG if `openml` is specified.

    :return: dataframe of data.
    """
    base, targets = datasets.fetch_openml("titanic", version=1, as_frame=True, return_X_y=True)
    df = pd.concat([base, targets], axis=1)
    return df


@extract_columns("pclass", "sex", "age", "parch", "sibsp", "fare", "embarked", "name", "survived")
@check_output(schema=passengers_df_schema, target_="passengers_df")
def passengers_df(raw_passengers_df: pd.DataFrame) -> pd.DataFrame:
    """Function to take in a raw dataframe, check the output, and then extract columns.

    :param raw_passengers_df: the raw dataset we want to bring in.
    :return:
    """
    raw_passengers_df = raw_passengers_df.set_index("pid")  # create new DF.
    raw_passengers_df.columns = _sanitize_columns(raw_passengers_df.columns)
    return raw_passengers_df


def target(survived: pd.Series) -> pd.Series:
    """Just hard coding this mapping that we want survived to be our target.

    :param survived:
    :return:
    """
    target_col = survived.copy()
    target_col.name = "target"
    return target_col
