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
import weaviate


def client_vector_db(vector_db_config: dict) -> weaviate.Client:
    """Instantiate Weaviate client using Environment and API key"""
    client = weaviate.Client(**vector_db_config)
    if client.is_live() and client.is_ready():
        return client
    else:
        raise ConnectionError("Error creating Weaviate client")


def initialize_vector_db_indices(client_vector_db: weaviate.Client) -> bool:
    """Initialize Weaviate by creating the class schema"""

    schema = {
        "class": "SQuADEntry",
        "description": "Entry from the SQuAD dataset",
        "vectorIndexType": "hnsw",
        "vectorizer": "none",
        "properties": [
            {
                "name": "squad_id",
                "dataType": ["string"],
                "description": "unique id from the SQuAD dataset",
            },
            {
                "name": "title",
                "dataType": ["text"],
                "description": "title column from the SQuAD dataset",
            },
            {
                "name": "context",
                "dataType": ["text"],
                "description": "context column from the SQuAD dataset",
            },
            {
                "name": "embedding_service",
                "dataType": ["string"],
                "description": "service used to create the embedding vector",
            },
            {
                "name": "model_name",
                "dataType": ["string"],
                "description": "model used by embedding service to create the vector",
            },
        ],
    }

    # do not overwrite if class exists
    if client_vector_db.schema.contains(schema):
        return

    client_vector_db.schema.create_class(schema)
    return True


def reset_vector_db(client_vector_db: weaviate.Client) -> bool:
    """Delete all schema and the data stored"""
    client_vector_db.schema.delete_all()
    return True


def data_objects(
    ids: list[str], titles: list[str], text_contents: list[str], metadata: dict
) -> list[dict]:
    """Create valid weaviate objects that match the defined schema"""
    assert len(ids) == len(titles) == len(text_contents)
    return [
        dict(squad_id=id_, title=title, context=context, **metadata)
        for id_, title, context in zip(ids, titles, text_contents)
    ]


def push_to_vector_db(
    client_vector_db: weaviate.Client,
    class_name: str,
    data_objects: list[dict],
    embeddings: list[np.ndarray],
    batch_size: int = 100,
) -> int:
    """Push batch of data objects with their respective embedding to Weaviate.
    Return number of objects.
    """
    assert len(data_objects) == len(embeddings)
    with client_vector_db.batch(batch_size=batch_size, dynamic=True) as batch:
        for i in range(len(data_objects)):
            batch.add_data_object(
                data_object=data_objects[i], class_name=class_name, vector=embeddings[i]
            )
    return len(data_objects)
