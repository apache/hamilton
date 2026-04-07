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
Hamilton ingestion DAG for the TMDB movie dataset.

Input files (place in data/):
  - tmdb_5000_movies.json   : movie metadata, genres, production companies
  - tmdb_5000_credits.json  : cast and crew per movie

The DAG produces a fully populated Neo4j knowledge graph with the schema
defined in graph_schema.py.

Node types   : Movie, Person, Genre, ProductionCompany
Relationships: ACTED_IN, DIRECTED, IN_GENRE, PRODUCED_BY

DAG flow:
    movies_path -> raw_movies -> parsed_movies  -> write_movie_nodes
                              -> genre_records   -> write_genre_nodes_and_edges
                              -> company_records -> write_company_nodes_and_edges
    credits_path -> raw_credits -> parsed_credits -> write_person_nodes_and_edges
    all writes -> ingestion_summary
"""

import json
import logging

from neo4j import Driver

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Load raw data
# ---------------------------------------------------------------------------


def raw_movies(movies_path: str) -> list[dict]:
    """Load raw movie records from the TMDB movies JSON file."""
    with open(movies_path) as f:
        data = json.load(f)
    logger.info("Loaded %d raw movie records", len(data))
    return data


def raw_credits(credits_path: str) -> list[dict]:
    """Load raw credit records from the TMDB credits JSON file."""
    with open(credits_path) as f:
        data = json.load(f)
    logger.info("Loaded %d raw credit records", len(data))
    return data


# ---------------------------------------------------------------------------
# 2. Parse movies
# ---------------------------------------------------------------------------


def parsed_movies(raw_movies: list[dict]) -> list[dict]:
    """
    Extract clean Movie node properties from raw records.
    Drops records missing id or title.
    """
    movies = []
    for m in raw_movies:
        if not m.get("id") or not m.get("title"):
            continue
        movies.append(
            {
                "id": int(m["id"]),
                "title": str(m["title"]),
                "release_date": str(m.get("release_date", "")),
                "overview": str(m.get("overview", "")),
                "popularity": float(m.get("popularity", 0.0)),
                "vote_average": float(m.get("vote_average", 0.0)),
            }
        )
    logger.info("Parsed %d movies", len(movies))
    return movies


def genre_records(raw_movies: list[dict]) -> list[dict]:
    """
    Extract (movie_id, genre_name) pairs for IN_GENRE relationships.
    Handles both pre-parsed lists and JSON-string encoded genres.
    """
    records = []
    for m in raw_movies:
        movie_id = m.get("id")
        if not movie_id:
            continue
        genres = m.get("genres", [])
        if isinstance(genres, str):
            try:
                genres = json.loads(genres)
            except json.JSONDecodeError:
                continue
        for g in genres:
            if g.get("name"):
                records.append({"movie_id": int(movie_id), "genre_name": str(g["name"])})
    logger.info("Extracted %d genre relationships", len(records))
    return records


def company_records(raw_movies: list[dict]) -> list[dict]:
    """
    Extract (movie_id, company_id, company_name) pairs for PRODUCED_BY relationships.
    Handles both pre-parsed lists and JSON-string encoded production_companies.
    """
    records = []
    for m in raw_movies:
        movie_id = m.get("id")
        if not movie_id:
            continue
        companies = m.get("production_companies", [])
        if isinstance(companies, str):
            try:
                companies = json.loads(companies)
            except json.JSONDecodeError:
                continue
        for c in companies:
            if c.get("id") and c.get("name"):
                records.append(
                    {
                        "movie_id": int(movie_id),
                        "company_id": int(c["id"]),
                        "company_name": str(c["name"]),
                    }
                )
    logger.info("Extracted %d production company relationships", len(records))
    return records


# ---------------------------------------------------------------------------
# 3. Parse credits
# ---------------------------------------------------------------------------


def parsed_credits(raw_credits: list[dict]) -> list[dict]:
    """
    Parse credits into a flat list of records containing movie_id,
    person details, and role (cast or director only from crew).
    Handles both pre-parsed lists and JSON-string encoded cast/crew fields.
    """
    records = []
    for c in raw_credits:
        movie_id = c.get("id") or c.get("movie_id")
        if not movie_id:
            continue

        cast = c.get("cast", [])
        if isinstance(cast, str):
            try:
                cast = json.loads(cast)
            except json.JSONDecodeError:
                cast = []
        for member in cast:
            if member.get("id") and member.get("name"):
                records.append(
                    {
                        "movie_id": int(movie_id),
                        "person_id": int(member["id"]),
                        "person_name": str(member["name"]),
                        "role": "cast",
                        "character": str(member.get("character", "")),
                        "order": int(member.get("order", 999)),
                    }
                )

        crew = c.get("crew", [])
        if isinstance(crew, str):
            try:
                crew = json.loads(crew)
            except json.JSONDecodeError:
                crew = []
        for member in crew:
            if member.get("job") == "Director" and member.get("id") and member.get("name"):
                records.append(
                    {
                        "movie_id": int(movie_id),
                        "person_id": int(member["id"]),
                        "person_name": str(member["name"]),
                        "role": "director",
                        "character": "",
                        "order": -1,
                    }
                )

    logger.info("Parsed %d credit records", len(records))
    return records


# ---------------------------------------------------------------------------
# 4. Write to Neo4j
# ---------------------------------------------------------------------------


def _run_batch(session, query: str, batch: list[dict]) -> int:
    """Execute a parameterised Cypher UNWIND query for a batch of records."""
    session.run(query, {"batch": batch})
    return len(batch)


def write_movie_nodes(parsed_movies: list[dict], neo4j_driver: Driver) -> int:
    """MERGE Movie nodes into Neo4j. Returns number of movies written."""
    query = """
    UNWIND $batch AS row
    MERGE (m:Movie {id: row.id})
    SET m.title        = row.title,
        m.release_date = row.release_date,
        m.overview     = row.overview,
        m.popularity   = row.popularity,
        m.vote_average = row.vote_average
    """
    with neo4j_driver.session() as session:
        count = _run_batch(session, query, parsed_movies)
    logger.info("Wrote %d Movie nodes", count)
    return count


def write_genre_nodes_and_edges(genre_records: list[dict], neo4j_driver: Driver) -> int:
    """MERGE Genre nodes and IN_GENRE relationships. Returns number of edges written."""
    query = """
    UNWIND $batch AS row
    MERGE (g:Genre {name: row.genre_name})
    WITH g, row
    MATCH (m:Movie {id: row.movie_id})
    MERGE (m)-[:IN_GENRE]->(g)
    """
    with neo4j_driver.session() as session:
        count = _run_batch(session, query, genre_records)
    logger.info("Wrote %d IN_GENRE edges", count)
    return count


def write_company_nodes_and_edges(company_records: list[dict], neo4j_driver: Driver) -> int:
    """MERGE ProductionCompany nodes and PRODUCED_BY relationships."""
    query = """
    UNWIND $batch AS row
    MERGE (c:ProductionCompany {id: row.company_id})
    SET c.name = row.company_name
    WITH c, row
    MATCH (m:Movie {id: row.movie_id})
    MERGE (m)-[:PRODUCED_BY]->(c)
    """
    with neo4j_driver.session() as session:
        count = _run_batch(session, query, company_records)
    logger.info("Wrote %d PRODUCED_BY edges", count)
    return count


def write_person_nodes_and_edges(parsed_credits: list[dict], neo4j_driver: Driver) -> int:
    """
    MERGE Person nodes and ACTED_IN / DIRECTED relationships.
    Returns total number of relationships written.
    """
    acted_in_query = """
    UNWIND $batch AS row
    MERGE (p:Person {id: row.person_id})
    SET p.name = row.person_name
    WITH p, row
    MATCH (m:Movie {id: row.movie_id})
    MERGE (p)-[r:ACTED_IN {order: row.order}]->(m)
    SET r.character = row.character
    """
    directed_query = """
    UNWIND $batch AS row
    MERGE (p:Person {id: row.person_id})
    SET p.name = row.person_name
    WITH p, row
    MATCH (m:Movie {id: row.movie_id})
    MERGE (p)-[:DIRECTED]->(m)
    """
    cast_records = [r for r in parsed_credits if r["role"] == "cast"]
    director_records = [r for r in parsed_credits if r["role"] == "director"]

    with neo4j_driver.session() as session:
        _run_batch(session, acted_in_query, cast_records)
        _run_batch(session, directed_query, director_records)

    total = len(cast_records) + len(director_records)
    logger.info(
        "Wrote %d ACTED_IN and %d DIRECTED edges",
        len(cast_records),
        len(director_records),
    )
    return total


# ---------------------------------------------------------------------------
# 5. Terminal node
# ---------------------------------------------------------------------------


def ingestion_summary(
    write_movie_nodes: int,
    write_genre_nodes_and_edges: int,
    write_company_nodes_and_edges: int,
    write_person_nodes_and_edges: int,
) -> dict:
    """
    Collect write counts from all upstream nodes and return a summary.
    Terminal node of the ingestion DAG.
    """
    summary = {
        "movies": write_movie_nodes,
        "genre_edges": write_genre_nodes_and_edges,
        "company_edges": write_company_nodes_and_edges,
        "person_edges": write_person_nodes_and_edges,
    }
    logger.info("Ingestion complete: %s", summary)
    return summary