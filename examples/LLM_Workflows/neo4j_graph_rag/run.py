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
Entry point for the Neo4j GraphRAG example.

Usage
-----
# Step 1 — ingest TMDB data into Neo4j
python run.py --mode ingest

# Step 2 — compute and store embeddings on Movie nodes
python run.py --mode embed

# Step 3 — ask questions against the populated graph
python run.py --mode query --question "Who directed Inception?"

# Visualise any DAG without executing
python run.py --mode ingest --visualise
python run.py --mode embed  --visualise
python run.py --mode query  --visualise
"""

import argparse
import logging
import os
from pathlib import Path

import embed_module
import generation_module
import ingest_module
import retrieval_module
from dotenv import load_dotenv
from graph_schema import CONSTRAINTS
from neo4j import GraphDatabase

from hamilton import driver

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def get_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return val


def make_neo4j_driver():
    uri = get_env("NEO4J_URI")
    user = get_env("NEO4J_USERNAME")
    password = get_env("NEO4J_PASSWORD")
    drv = GraphDatabase.driver(uri, auth=(user, password))
    drv.verify_connectivity()
    logger.info("Connected to Neo4j at %s", uri)
    return drv


def apply_constraints(drv):
    with drv.session() as session:
        for constraint in CONSTRAINTS:
            session.run(constraint)
    logger.info("Applied %d constraints", len(CONSTRAINTS))


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------


def run_ingest(visualise: bool = False):
    data_dir = Path(__file__).parent / "data"
    movies_path = str(data_dir / "tmdb_5000_movies.json")
    credits_path = str(data_dir / "tmdb_5000_credits.json")

    for p in [movies_path, credits_path]:
        if not Path(p).exists():
            raise FileNotFoundError(
                f"Missing data file: {p}\n"
                "Download from https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata "
                "and place both JSON files in the data/ folder.\n"
                "See data/README.md for conversion instructions."
            )

    drv = make_neo4j_driver()
    apply_constraints(drv)

    ingest_driver = driver.Builder().with_modules(ingest_module).build()

    if visualise:
        ingest_driver.display_all_functions("ingest_dag.png")
        logger.info("Saved ingest DAG visualisation to ingest_dag.png")
        drv.close()
        return

    result = ingest_driver.execute(
        ["ingestion_summary"],
        inputs={
            "movies_path": movies_path,
            "credits_path": credits_path,
            "neo4j_driver": drv,
        },
    )
    s = result["ingestion_summary"]
    logger.info(
        "Ingestion complete — movies: %d, genre edges: %d, company edges: %d, person edges: %d",
        s["movies"],
        s["genre_edges"],
        s["company_edges"],
        s["person_edges"],
    )
    drv.close()


# ---------------------------------------------------------------------------
# embed
# ---------------------------------------------------------------------------


def run_embed(visualise: bool = False):
    drv = make_neo4j_driver()
    openai_api_key = get_env("OPENAI_API_KEY")

    embed_driver = driver.Builder().with_modules(embed_module).build()

    if visualise:
        embed_driver.display_all_functions("embed_dag.png")
        logger.info("Saved embed DAG visualisation to embed_dag.png")
        drv.close()
        return

    result = embed_driver.execute(
        ["embedding_summary"],
        inputs={
            "neo4j_driver": drv,
            "openai_api_key": openai_api_key,
        },
    )
    s = result["embedding_summary"]
    logger.info(
        "Embedding complete — %d embeddings written, index: %s, model: %s",
        s["embeddings_written"],
        s["vector_index"],
        s["model"],
    )
    drv.close()


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


def run_query(question: str, visualise: bool = False):
    drv = make_neo4j_driver()
    openai_api_key = get_env("OPENAI_API_KEY")

    rag_driver = driver.Builder().with_modules(retrieval_module, generation_module).build()

    if visualise:
        rag_driver.display_all_functions("rag_dag.png")
        logger.info("Saved RAG DAG visualisation to rag_dag.png")
        drv.close()
        return

    result = rag_driver.execute(
        ["answer"],
        inputs={
            "user_query": question,
            "neo4j_driver": drv,
            "openai_api_key": openai_api_key,
        },
    )
    print("\n" + "=" * 60)
    print(f"Q: {question}")
    print("=" * 60)
    print(f"A: {result['answer']}")
    print("=" * 60 + "\n")
    drv.close()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Neo4j GraphRAG — TMDB Movies")
    parser.add_argument(
        "--mode",
        choices=["ingest", "embed", "query"],
        required=True,
        help=(
            "ingest: load TMDB data into Neo4j | "
            "embed: compute and store embeddings | "
            "query: ask a question"
        ),
    )
    parser.add_argument(
        "--question",
        type=str,
        default="Which movies did Christopher Nolan direct?",
        help="Question to ask (only used in query mode)",
    )
    parser.add_argument(
        "--visualise",
        action="store_true",
        help="Save a PNG of the Hamilton DAG and exit without executing",
    )
    args = parser.parse_args()

    if args.mode == "ingest":
        run_ingest(visualise=args.visualise)
    elif args.mode == "embed":
        run_embed(visualise=args.visualise)
    elif args.mode == "query":
        run_query(question=args.question, visualise=args.visualise)


if __name__ == "__main__":
    main()
