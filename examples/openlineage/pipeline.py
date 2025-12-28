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

import pickle
from typing import Tuple

import pandas as pd

from hamilton.function_modifiers import dataloader, datasaver
from hamilton.io import utils

"""
Narrative:
 - this is a pipeline that will be used to show open lineage integration
 - one function loads from file
 - another loads from a database
 - one save to a file
 - another saves to a database
 - there are transform functions in between
"""


@dataloader()
def user_dataset(file_ds_path: str) -> Tuple[pd.DataFrame, dict]:
    df = pd.read_csv(file_ds_path)
    return df, utils.get_file_and_dataframe_metadata(file_ds_path, df)


@dataloader()
def purchase_dataset(db_client: object) -> Tuple[pd.DataFrame, dict]:
    query = "SELECT * FROM purchase_data"
    df = pd.read_sql(query, con=db_client)
    metadata = {
        "sql_metadata": {"query": query, "table_name": "purchase_data", "database": "sqlite"}
    }
    metadata.update(utils.get_dataframe_metadata(df))
    return df, metadata


def transformed_user_dataset(user_dataset: pd.DataFrame) -> pd.DataFrame:
    return user_dataset


def transformed_purchase_dataset(purchase_dataset: pd.DataFrame) -> pd.DataFrame:
    return purchase_dataset


def joined_dataset(
    transformed_user_dataset: pd.DataFrame, transformed_purchase_dataset: pd.DataFrame
) -> pd.DataFrame:
    joined = pd.merge(
        transformed_user_dataset, transformed_purchase_dataset, left_on="id", right_on="user_id"
    )
    del joined["id_x"]
    del joined["id_y"]
    return joined


class ModelObject:
    def __init__(self):
        pass

    def predict(self, data):
        return data + 1


def fit_model(joined_dataset: pd.DataFrame) -> ModelObject:
    # model = ...
    return ModelObject()


@datasaver()
def saved_file(fit_model: ModelObject, file_path: str) -> dict:
    with open(file_path, "wb") as f:
        pickle.dump(fit_model, f)
    return utils.get_file_metadata(file_path)


@datasaver()
def saved_to_db(joined_dataset: pd.DataFrame, db_client: object, joined_table_name: str) -> dict:
    joined_dataset.to_sql(joined_table_name, con=db_client, index=False, if_exists="replace")
    # raise ValueError("Hi")
    metadata = utils.get_sql_metadata(joined_table_name, joined_dataset)
    metadata.update(utils.get_dataframe_metadata(joined_dataset))
    return metadata


if __name__ == "__main__":
    import sqlite3

    from openlineage.client import OpenLineageClient
    from openlineage.client.transport.file import FileConfig, FileTransport

    import __main__ as pipeline
    from hamilton import driver
    from hamilton.plugins import h_openlineage

    file_config = FileConfig(
        log_file_path="pipeline.json",
        append=True,
    )

    # client = OpenLineageClient(url="http://localhost:9000")
    client = OpenLineageClient(transport=FileTransport(file_config))

    ola = h_openlineage.OpenLineageAdapter(client, "demo_namespace", "hamilton_job")

    db_client = sqlite3.connect("purchase_data.db")

    dr = driver.Builder().with_modules(pipeline).with_adapters(ola).build()
    dr.display_all_functions("graph.png")
    result = dr.execute(
        ["saved_file", "saved_to_db"],
        inputs={
            "db_client": db_client,
            "file_ds_path": "data.csv",
            "file_path": "model.pkl",
            "joined_table_name": "joined_data",
        },
    )

    db_client.close()
