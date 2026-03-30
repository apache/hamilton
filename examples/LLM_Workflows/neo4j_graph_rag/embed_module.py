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
Hamilton embedding DAG.

Fetches Movie nodes from Neo4j, computes OpenAI embeddings over
title + overview text, writes embeddings back to each node, and
creates a Neo4j vector index for use during retrieval.

Run this once after ingestion and before querying.

DAG flow:
    neo4j_driver + openai_api_key
        -> movie_texts
        -> embedding_client
        -> movie_embeddings
        -> vector_index
        -> embedding_summary
"""

import logging

import openai
from neo4j import Driver

logger = logging.getLogger(__name__)

# Shared constants — also imported by retrieval_module.py
VECTOR_INDEX_NAME = "movie_embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100


def movie_texts(neo4j_driver: Driver) -> list[dict]:
    """
    Fetch all Movie nodes and build embedding text from title + overview.
    Returns list of dicts with keys: id, text.
    """
    query = """
    MATCH (m:Movie)
    WHERE m.title IS NOT NULL
    RETURN m.id AS id,
           m.title AS title,
           coalesce(m.overview, '') AS overview
    """
    with neo4j_driver.session() as session:
        rows = session.run(query).data()

    texts = [
        {
            "id": row["id"],
            "text": f"{row['title']}. {row['overview']}".strip(),
        }
        for row in rows
        if row["id"] is not None
    ]
    logger.info("Fetched %d movie texts for embedding", len(texts))
    return texts


def embedding_client(openai_api_key: str) -> openai.OpenAI:
    """Initialise the OpenAI client for embedding calls."""
    return openai.OpenAI(api_key=openai_api_key)


def movie_embeddings(
    movie_texts: list[dict],
    embedding_client: openai.OpenAI,
) -> list[dict]:
    """
    Compute OpenAI embeddings for all movie texts in batches of BATCH_SIZE.
    Returns list of dicts with keys: id, embedding.
    """
    results = []
    total = len(movie_texts)

    for i in range(0, total, BATCH_SIZE):
        batch = movie_texts[i : i + BATCH_SIZE]
        response = embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[item["text"] for item in batch],
        )
        for item, emb_obj in zip(batch, response.data):
            results.append({"id": item["id"], "embedding": emb_obj.embedding})

        logger.info("Embedded batch %d-%d of %d", i, min(i + BATCH_SIZE, total), total)

    logger.info("Computed %d embeddings", len(results))
    return results


def vector_index(
    movie_embeddings: list[dict],
    neo4j_driver: Driver,
) -> str:
    """
    Write embeddings to Movie nodes in Neo4j and create a cosine
    vector index named VECTOR_INDEX_NAME over the embedding property.
    Returns the index name.
    """
    write_query = """
    UNWIND $batch AS row
    MATCH (m:Movie {id: row.id})
    SET m.embedding = row.embedding
    """
    total = len(movie_embeddings)
    with neo4j_driver.session() as session:
        for i in range(0, total, BATCH_SIZE):
            batch = movie_embeddings[i : i + BATCH_SIZE]
            session.run(write_query, {"batch": batch})
            logger.info(
                "Wrote embeddings to nodes %d-%d of %d",
                i,
                min(i + BATCH_SIZE, total),
                total,
            )

        session.run(f"DROP INDEX {VECTOR_INDEX_NAME} IF EXISTS")
        session.run(
            f"""
            CREATE VECTOR INDEX {VECTOR_INDEX_NAME}
            FOR (m:Movie)
            ON m.embedding
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {EMBEDDING_DIMENSIONS},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
        )
        logger.info("Created vector index '%s'", VECTOR_INDEX_NAME)

    return VECTOR_INDEX_NAME


def embedding_summary(
    movie_embeddings: list[dict],
    vector_index: str,
) -> dict:
    """
    Collect embedding statistics and return a summary.
    Terminal node of the embedding DAG.
    """
    summary = {
        "embeddings_written": len(movie_embeddings),
        "vector_index": vector_index,
        "model": EMBEDDING_MODEL,
        "dimensions": EMBEDDING_DIMENSIONS,
    }
    logger.info("Embedding complete: %s", summary)
    return summary