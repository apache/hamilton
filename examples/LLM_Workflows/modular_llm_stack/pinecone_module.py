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

from types import ModuleType

import numpy as np
import pinecone


def client_vector_db(vector_db_config: dict) -> ModuleType:
    """Instantiate Pinecone client using Environment and API key"""
    pinecone.init(**vector_db_config)
    return pinecone


def index_name(class_name: str) -> str:
    """Convert class_name to valid pinecone index_name"""
    return class_name.lower()


def initialize_vector_db_indices(
    client_vector_db: ModuleType,
    index_name: str,
    embedding_dimension: int,
    embedding_metric: str,
) -> bool:
    """Initialize Pinecone by creating the index"""

    # do not overwrite if class exists
    if index_name not in client_vector_db.list_indexes():
        client_vector_db.create_index(
            index_name, dimension=embedding_dimension, metric=embedding_metric
        )
    return True


def reset_vector_db(client_vector_db: ModuleType) -> bool:
    """Delete the entire index and the data stored"""
    for idx in client_vector_db.list_indexes():
        client_vector_db.delete_index(idx)
    return True


def data_objects(
    ids: list[str], titles: list[str], embeddings: list[np.ndarray], metadata: dict
) -> list[tuple]:
    """Create valid pinecone objects (index, vector, metadata) tuples for upsert"""
    assert len(ids) == len(titles) == len(embeddings)
    properties = [dict(title=title, **metadata) for title in titles]
    embeddings = [x.tolist() for x in embeddings]
    return list(zip(ids, embeddings, properties))


def push_to_vector_db(
    client_vector_db: ModuleType,
    index_name: str,
    data_objects: list[tuple],
    batch_size: int = 100,
) -> int:
    """Upsert objects to Pinecone index; return the number of objects inserted"""
    pinecone_index = pinecone.Index(index_name)

    for i in range(0, len(data_objects), batch_size):
        i_end = min(i + batch_size, len(data_objects))

        pinecone_index.upsert(vectors=data_objects[i:i_end])
    return len(data_objects)
