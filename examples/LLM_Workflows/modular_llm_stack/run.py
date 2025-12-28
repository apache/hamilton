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

from __future__ import annotations

import json

import click
import data_module
import embedding_module

from hamilton import base, driver


@click.command()
@click.option(
    "--vector_db",
    type=click.Choice(["lancedb", "weaviate", "pinecone", "marqo", "qdrant"], case_sensitive=False),
    default="lancedb",
    help="Vector database service",
)
@click.option(
    "--vector_db_config",
    default='{"uri": "data/lancedb"}',
    help="Pass a JSON string for vector database config.\
        Weaviate needs a dictionary {'url': ''}\
        Pinecone needs dictionary {'environment': '', 'api_key': ''}",
)
@click.option(
    "--embedding_service",
    type=click.Choice(
        ["openai", "cohere", "sentence_transformer", "marqo", "fastembed"], case_sensitive=False
    ),
    default="sentence_transformer",
    help="Text embedding service.",
)
@click.option(
    "--embedding_service_api_key",
    default=None,
    help="API Key for embedding service. Needed if using OpenAI or Cohere.",
)
@click.option("--model_name", default=None, help="Text embedding model name.")
@click.option("--display_dag", is_flag=True, help="Generate a .png of the Hamilton DAG")
@click.option(
    "--other_input_kwargs", default=None, help="Pass in other input kwargs as a JSON string."
)
def main(
    vector_db: str,
    vector_db_config: str,
    embedding_service: str,
    embedding_service_api_key: str | None,
    model_name: str,
    display_dag: bool,
    other_input_kwargs: str,
):
    if vector_db == "weaviate":
        import weaviate_module

        vector_db_module = weaviate_module
    elif vector_db == "pinecone":
        import pinecone_module

        vector_db_module = pinecone_module
    elif vector_db == "lancedb":
        import lancedb_module

        vector_db_module = lancedb_module
    elif vector_db == "marqo":
        import marqo_module

        vector_db_module = marqo_module
    elif vector_db == "qdrant":
        import qdrant_module

        vector_db_module = qdrant_module

    else:
        raise ValueError(f"Unknown vector_db {vector_db}")

    if model_name is None:
        if embedding_service == "openai":
            model_name = "text-embedding-ada-002"
        elif embedding_service == "cohere":
            model_name = "embed-english-light-v2.0"
        elif embedding_service == "sentence_transformer":
            model_name = "multi-qa-MiniLM-L6-cos-v1"
        elif embedding_service == "fastembed":
            model_name = "BAAI/bge-small-en-v1.5"

    config = dict(
        vector_db_config=json.loads(vector_db_config),
        embedding_service=embedding_service,  # this triggers config.when() in embedding_module
        api_key=embedding_service_api_key,
        model_name=model_name,
    )

    if other_input_kwargs is None:
        other_input_kwargs = "{}"
    input_dict = json.loads(other_input_kwargs)
    input_dict.update(dict(class_name="SQuADEntry"))

    dr = driver.Driver(
        config,
        data_module,
        vector_db_module,  # this points to one of the VectorDB modules
        embedding_module,
        adapter=base.DefaultAdapter(),
    )

    # The `final_vars` requested are functions with side-effects
    dr.execute(
        final_vars=["initialize_vector_db_indices", "push_to_vector_db"],
        inputs=input_dict,
    )

    if display_dag:
        filename = f"{vector_db}_{embedding_service}_dag"
        dr.display_all_functions(filename, {"format": "png"})


if __name__ == "__main__":
    main()
