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

import logging
from typing import Any, Union

import marqo

logger = logging.getLogger(__name__)


def client_vector_db(vector_db_config: dict) -> marqo.Client:
    """Instantiate Marqo client using Environment and API key"""
    mq = marqo.Client(**vector_db_config)
    return mq


def initialize_vector_db_indices(
    client_vector_db: marqo.Client,
    index_name: str,
) -> bool:
    """Initialize Marqo by creating the index"""
    indexes = [index.index_name for index in client_vector_db.get_indexes()["results"]]
    if index_name not in indexes:
        client_vector_db.create_index(index_name)
        logging.info(f"Created index '{index_name}'")
    return True


def reset_vector_db(client_vector_db: marqo.Client) -> bool:
    """Delete the entire index and the data stored"""
    indexes = [index.index_name for index in client_vector_db.get_indexes()["results"]]

    for idx in indexes:
        client_vector_db.delete_index(idx)
    return True


def data_objects(
    ids: list[str],
    titles: list[str],
    text_contents: list[str],
) -> list[dict]:
    assert len(ids) == len(titles) == len(text_contents)
    return [
        dict(_id=id, title=title, Description=text_content)
        for id, title, text_content in zip(ids, titles, text_contents)
        if id is not None and title is not None or text_content is not None
    ]


def push_to_vector_db(
    client_vector_db: marqo.Client,
    index_name: str,
    data_objects: list[dict],
) -> int:
    response = client_vector_db.index(index_name).add_documents(
        data_objects, tensor_fields=["title", "Description"]
    )
    if isinstance(response, dict):
        response = [response]
    for batch in response:
        if "errors" in batch and batch["errors"]:
            logger.error(batch)
            raise Exception(f"Failed to add documents to index {index_name}: {batch['errors']}")
    return True


if __name__ == "__main__":
    # This functionality below will not work until the Marqo server is running, and you've
    # run `run.py` to populate it with data.

    import pprint

    def query_vector_db(
        client_vector_db: marqo.Client,
        index_name: str,
        query: str,
        top_k: int = 10,
        include_metadata: bool = True,
        include_vectors: bool = False,
        namespace: str = None,
    ) -> list[dict[str, Union[Union[list[Any], dict], Any]]]:
        params = {
            "limit": top_k,
            "attributes_to_retrieve": ["*"] if include_metadata else ["_id"],
            "filter_string": f"namespace:{namespace}" if namespace else None,
        }

        results = client_vector_db.index(index_name).search(query, **params)

        if include_vectors:
            results["hits"] = [
                {
                    **r,
                    **client_vector_db.index(index_name).get_document(r["_id"], expose_facets=True),
                }
                for r in results["hits"]
            ]

        results_list = [
            {
                "vector": r["_tensor_facets"][0]["_embedding"] if include_vectors else [],
                "score": r["_score"],
                "meta": {k: v for k, v in r.items() if k not in ["_score", "_tensor_facets"]},
            }
            for r in results["hits"]
        ]

        return results_list

    _client = client_vector_db({"url": "http://localhost:8882"})
    _result = query_vector_db(_client, "hamilton", "Catholic character", 10, True, True, None)
    pprint.pprint(_result)
