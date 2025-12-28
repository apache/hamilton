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

import lancedb
import numpy as np
import pandas as pd
import pyarrow as pa


def client_vector_db(vector_db_config: dict) -> lancedb.LanceDBConnection:
    """Connect to a lancedb instance"""
    return lancedb.connect(**vector_db_config)


def initialize_vector_db_indices(
    client_vector_db: lancedb.LanceDBConnection,
    class_name: str,
    embedding_dimension: int,
) -> bool:
    """Initialize the LanceDB table;
    NOTE this pattern currently doesn't work and is due to a bug with lancedb
    """
    schema = pa.schema(
        [
            ("squad_id", pa.string()),
            ("title", pa.string()),
            ("context", pa.string()),
            ("embedding_service", pa.string()),
            ("model_name", pa.string()),
            pa.field("vector", type=pa.list_(pa.float32(), list_size=embedding_dimension)),
        ]
    )

    client_vector_db.create_table(name=class_name, schema=schema, mode="create")

    return True


def reset_vector_db(client_vector_db: lancedb.LanceDBConnection) -> bool:
    """Delete all tables from the database"""
    for table_name in client_vector_db.table_names():
        client_vector_db.drop_table(table_name)
    return True


def data_objects(
    ids: list[str],
    titles: list[str],
    text_contents: list[str],
    embeddings: list[np.ndarray],
    metadata: dict,
) -> list[dict]:
    """Create valid LanceDB objects"""
    assert len(ids) == len(titles) == len(text_contents) == len(embeddings)
    return [
        dict(squad_id=id_, title=title, context=context, vector=embedding, **metadata)
        for id_, title, context, embedding in zip(ids, titles, text_contents, embeddings)
    ]


def push_to_vector_db(
    client_vector_db: lancedb.LanceDBConnection,
    class_name: str,
    data_objects: list[dict],
    embedding_metric: str = "cosine",
) -> int:
    """Push dataframe of objects to LanceDB.
    Return number of objects.
    """
    df = pd.DataFrame.from_records(data_objects)
    table = client_vector_db.create_table(name=class_name, data=df, mode="overwrite")

    return table.to_pandas().shape[0]
