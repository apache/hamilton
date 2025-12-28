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

import numpy as np
from qdrant_client import QdrantClient, models


def client_vector_db(vector_db_config: dict) -> QdrantClient:
    return QdrantClient(**vector_db_config)


def initialize_vector_db_indices(
    client_vector_db: QdrantClient,
    class_name: str,
    embedding_dimension: int,
) -> bool:
    if client_vector_db.collection_exists(class_name):
        client_vector_db.delete_collection(class_name)

    client_vector_db.create_collection(
        class_name,
        vectors_config=models.VectorParams(
            size=embedding_dimension, distance=models.Distance.COSINE
        ),
    )

    return True


def reset_vector_db(client_vector_db: QdrantClient) -> bool:
    for collection in client_vector_db.get_collections().collections:
        client_vector_db.delete_collection(collection.name)
    return True


def data_objects(
    ids: list[str],
    titles: list[str],
    text_contents: list[str],
    embeddings: list[np.ndarray],
    metadata: dict,
) -> dict:
    assert len(ids) == len(titles) == len(embeddings)
    # Qdrant only allows unsigned integers and UUIDs as point IDs
    ids = list(range(len(ids)))
    payloads = [
        dict(id=_id, text_content=text_content, title=title, **metadata)
        for _id, title, text_content in zip(ids, titles, text_contents)
    ]
    embeddings = [x.tolist() for x in embeddings]
    return dict(ids=ids, vectors=embeddings, payload=payloads)


def push_to_vector_db(
    client_vector_db: QdrantClient,
    class_name: str,
    data_objects: dict,
) -> None:
    client_vector_db.upload_collection(class_name, **data_objects)
