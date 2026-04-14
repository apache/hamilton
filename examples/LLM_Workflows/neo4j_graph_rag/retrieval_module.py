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
Hamilton retrieval DAG — semantic entity resolution + multi-strategy GraphRAG.

Pipeline:
  1. query_intent       — classify into VECTOR / CYPHER / AGGREGATE / HYBRID
  2. entity_extraction  — LLM extracts named entities from the query
  3. entity_resolution  — each entity is looked up in Neo4j to get its
                          canonical form (exact name, genre spelling, date format)
  4. cypher_query       — Cypher is generated using resolved entities, not raw text
  5. cypher_results     — execute and return rows
  6. vector_results     — semantic similarity search (VECTOR / HYBRID only)
  7. merged_results     — combine both paths
  8. retrieved_context  — format for generation DAG
"""

import json
import logging

import openai
from embed_module import EMBEDDING_MODEL, VECTOR_INDEX_NAME
from graph_schema import schema_to_prompt
from neo4j import Driver

logger = logging.getLogger(__name__)

TOP_K = 8
MAX_CAST = 8
MAX_RETRIES = 2
SCHEMA_PROMPT = schema_to_prompt()

# ---------------------------------------------------------------------------
# Cypher examples used in generation prompt
# ---------------------------------------------------------------------------

CYPHER_EXAMPLES = """
-- Direct lookup (always return person/movie names explicitly)
MATCH (d:Person)-[:DIRECTED]->(m:Movie)
WHERE toLower(m.title) = toLower('Inception')
RETURN m.title AS movie, d.name AS director, m.release_date, m.vote_average

-- Actor filmography (always alias person name)
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
WHERE p.name = 'Tom Hanks'
RETURN p.name AS actor, m.title AS movie, m.release_date
ORDER BY m.release_date DESC
LIMIT 20

-- Director filmography
MATCH (p:Person)-[:DIRECTED]->(m:Movie)
WHERE p.name = 'Christopher Nolan'
RETURN p.name AS director, m.title AS movie, m.release_date, m.vote_average
ORDER BY m.release_date

-- Co-occurrence (use exact resolved names)
MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(b:Person {name: 'Robin Wright'})
RETURN m.title AS movie, m.release_date

-- Aggregation with minimum count to avoid single-film outliers
MATCH (d:Person)-[:DIRECTED]->(m:Movie)
WITH d, avg(m.vote_average) AS avg_rating, count(m) AS film_count
WHERE film_count >= 3
RETURN d.name AS director, avg_rating, film_count
ORDER BY avg_rating DESC
LIMIT 10

-- Production company (use exact resolved name)
MATCH (c:ProductionCompany {name: 'Warner Bros. Pictures'})<-[:PRODUCED_BY]-(m:Movie)
RETURN m.title AS movie, m.release_date
ORDER BY m.release_date DESC
LIMIT 20

-- Genre filter (use exact resolved genre name, string date comparison)
MATCH (m:Movie)-[:IN_GENRE]->(g:Genre {name: 'Comedy'})
WHERE m.vote_average > 7
  AND m.release_date > '2010-12-31'
RETURN m.title AS movie, m.release_date, m.vote_average
ORDER BY m.vote_average DESC
LIMIT 20

-- Multi-hop: always include connecting film titles for context
MATCH (a:Person)-[:ACTED_IN]->(m1:Movie)<-[:DIRECTED]-(d1:Person {name: 'Christopher Nolan'})
     ,(a)-[:ACTED_IN]->(m2:Movie)<-[:DIRECTED]-(d2:Person {name: 'Steven Spielberg'})
RETURN DISTINCT a.name AS actor, m1.title AS nolan_film, m2.title AS spielberg_film
LIMIT 20

-- Hybrid: director + genre + rating
MATCH (d:Person {name: 'James Cameron'})-[:DIRECTED]->(m:Movie)-[:IN_GENRE]->(g:Genre {name: 'Science Fiction'})
RETURN m.title AS movie, m.vote_average, d.name AS director
ORDER BY m.vote_average DESC
LIMIT 20

-- Highest rated overall or by genre (ALWAYS add popularity > 5 to exclude obscure films)
MATCH (m:Movie)-[:IN_GENRE]->(g:Genre {name: 'Drama'})
WHERE m.popularity > 5
RETURN m.title AS movie, m.vote_average
ORDER BY m.vote_average DESC
LIMIT 1

-- Highest rated film overall (ALWAYS add popularity > 5)
MATCH (m:Movie)
WHERE m.popularity > 5
RETURN m.title AS movie, m.vote_average
ORDER BY m.vote_average DESC
LIMIT 1
"""


# ---------------------------------------------------------------------------
# 1. Classify query intent
# ---------------------------------------------------------------------------


def query_intent(user_query: str, openai_api_key: str) -> str:
    """
    Classify the user query into one of four retrieval strategies:
      VECTOR    — thematic/semantic (recommend, find similar, what movies about X)
      CYPHER    — relational facts (who directed X, filmography, co-stars, direct lookup)
      AGGREGATE — counting/ranking across the dataset
      HYBRID    — needs both graph facts AND semantic similarity / filtering
    """
    system = """You are a query classifier for a movie knowledge graph.
Classify the user query into exactly one of these retrieval strategies:

VECTOR    — thematic or semantic: recommendations, "find movies like X",
            "movies about space", "psychological thrillers"
CYPHER    — relational or factual: "who directed X", "what movies did actor Y appear in",
            "did A and B appear together", "movies by director Z",
            "what year was X released", "who starred in X"
AGGREGATE — counting, ranking, aggregation: "which company made the most action movies",
            "highest rated drama", "director with highest average rating",
            "how many movies did X direct"
HYBRID    — needs both graph traversal AND filtering/rating:
            "highest rated sci-fi films by James Cameron",
            "Tom Hanks movies rated above 7.5",
            "comedy films after 2010 rated above 7"

Reply with ONLY one word: VECTOR, CYPHER, AGGREGATE, or HYBRID."""

    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_query},
        ],
        temperature=0.0,
        max_tokens=10,
    )
    intent = response.choices[0].message.content.strip().upper()
    if intent not in ("VECTOR", "CYPHER", "AGGREGATE", "HYBRID"):
        logger.warning("Unexpected intent '%s', defaulting to HYBRID", intent)
        intent = "HYBRID"
    logger.info("Query intent: %s", intent)
    return intent


# ---------------------------------------------------------------------------
# 2. Entity extraction
# ---------------------------------------------------------------------------


def entity_extraction(
    user_query: str,
    openai_api_key: str,
    query_intent: str,
) -> dict:
    """
    Extract named entities from the user query as a structured dict.
    Returns empty dict for VECTOR queries (no entity resolution needed).

    Entity types extracted:
      movies      : list of movie titles mentioned
      persons     : list of person names (actors, directors)
      genres      : list of genres mentioned
      companies   : list of production company names mentioned
      year_after  : year string if query filters by "after YYYY"
      year_before : year string if query filters by "before YYYY"
      rating_above: float if query filters by minimum rating
      rating_below: float if query filters by maximum rating
    """
    if query_intent == "VECTOR":
        logger.info("Skipping entity extraction for VECTOR intent")
        return {}

    system = """You are an entity extractor for a movie knowledge graph query system.

Extract all named entities from the user query and return a JSON object with these keys
(omit keys that are not present in the query):

{
  "movies":       ["title1", "title2"],
  "persons":      ["name1", "name2"],
  "genres":       ["genre1"],
  "companies":    ["company name"],
  "year_after":   "YYYY",
  "year_before":  "YYYY",
  "rating_above": 7.5,
  "rating_below": 8.0
}

Rules:
- Extract exactly what is in the query, do not normalise or correct spellings yet
- If a name could be an actor or director, put it in "persons"
- Return ONLY valid JSON, no explanation, no markdown fences"""

    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_query},
        ],
        temperature=0.0,
        max_tokens=300,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    try:
        entities = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse entity extraction response: %s", raw)
        entities = {}

    logger.info("Extracted entities: %s", entities)
    return entities


# ---------------------------------------------------------------------------
# 3. Entity resolution — look up canonical forms in Neo4j
# ---------------------------------------------------------------------------


def _resolve_persons(names: list[str], session) -> dict[str, str]:
    """Fuzzy-match person names against the graph, return {input: canonical}."""
    resolved = {}
    for name in names:
        result = session.run(
            """
            MATCH (p:Person)
            WHERE toLower(p.name) CONTAINS toLower($name)
            RETURN p.name AS name
            ORDER BY size(p.name)
            LIMIT 1
            """,
            {"name": name},
        ).single()
        if result:
            resolved[name] = result["name"]
            logger.info("Resolved person '%s' -> '%s'", name, result["name"])
        else:
            resolved[name] = name
            logger.warning("Could not resolve person '%s', using as-is", name)
    return resolved


def _resolve_movies(titles: list[str], session) -> dict[str, str]:
    """Fuzzy-match movie titles against the graph, return {input: canonical}."""
    resolved = {}
    for title in titles:
        result = session.run(
            """
            MATCH (m:Movie)
            WHERE toLower(m.title) CONTAINS toLower($title)
            RETURN m.title AS title
            ORDER BY size(m.title)
            LIMIT 1
            """,
            {"title": title},
        ).single()
        if result:
            resolved[title] = result["title"]
            logger.info("Resolved movie '%s' -> '%s'", title, result["title"])
        else:
            resolved[title] = title
            logger.warning("Could not resolve movie '%s', using as-is", title)
    return resolved


GENRE_ALIASES = {
    "sci-fi": "Science Fiction",
    "scifi": "Science Fiction",
    "science fiction": "Science Fiction",
    "rom-com": "Romance",
    "romcom": "Romance",
    "rom com": "Romance",
    "action-adventure": "Action",
    "documentary": "Documentary",
    "doc": "Documentary",
    "animated": "Animation",
    "animation": "Animation",
    "anime": "Animation",
    "horror": "Horror",
    "comedy": "Comedy",
    "drama": "Drama",
    "thriller": "Thriller",
    "western": "Western",
    "fantasy": "Fantasy",
    "mystery": "Mystery",
    "adventure": "Adventure",
    "crime": "Crime",
    "family": "Family",
    "history": "History",
    "music": "Music",
    "romance": "Romance",
    "war": "War",
    "tv movie": "TV Movie",
}


def _resolve_genres(genres: list[str], session) -> dict[str, str]:
    """
    Resolve genre names to their canonical form in the graph.
    First checks a local alias map for common abbreviations (e.g. sci-fi),
    then falls back to fuzzy Neo4j lookup.
    Returns {input: canonical}.
    """
    resolved = {}
    for genre in genres:
        # Check alias map first
        alias = GENRE_ALIASES.get(genre.lower())
        if alias:
            resolved[genre] = alias
            logger.info("Resolved genre '%s' -> '%s' (alias map)", genre, alias)
            continue

        # Fall back to fuzzy Neo4j lookup
        result = session.run(
            """
            MATCH (g:Genre)
            WHERE toLower(g.name) CONTAINS toLower($genre)
            RETURN g.name AS name
            LIMIT 1
            """,
            {"genre": genre},
        ).single()
        if result:
            resolved[genre] = result["name"]
            logger.info("Resolved genre '%s' -> '%s'", genre, result["name"])
        else:
            resolved[genre] = genre
            logger.warning("Could not resolve genre '%s', using as-is", genre)
    return resolved


def _resolve_companies(companies: list[str], session) -> dict[str, str]:
    """Fuzzy-match company names against the graph, return {input: canonical}."""
    resolved = {}
    for company in companies:
        result = session.run(
            """
            MATCH (c:ProductionCompany)
            WHERE toLower(c.name) CONTAINS toLower($company)
            RETURN c.name AS name
            ORDER BY size(c.name)
            LIMIT 1
            """,
            {"company": company},
        ).single()
        if result:
            resolved[company] = result["name"]
            logger.info("Resolved company '%s' -> '%s'", company, result["name"])
        else:
            resolved[company] = company
            logger.warning("Could not resolve company '%s', using as-is", company)
    return resolved


def entity_resolution(
    entity_extraction: dict,
    neo4j_driver: Driver,
    query_intent: str,
) -> dict:
    """
    Resolve each extracted entity to its canonical form in Neo4j.

    Returns the same structure as entity_extraction but with values
    replaced by their canonical graph names. Also normalises:
      - year_after  -> date string '>YYYY-01-01' for Cypher comparison
      - year_before -> date string '<YYYY-12-31'
      - rating_above/below -> kept as floats
    """
    if query_intent == "VECTOR" or not entity_extraction:
        return entity_extraction

    resolved = {}

    with neo4j_driver.session() as session:
        if entity_extraction.get("persons"):
            resolved["persons"] = _resolve_persons(entity_extraction["persons"], session)

        if entity_extraction.get("movies"):
            resolved["movies"] = _resolve_movies(entity_extraction["movies"], session)

        if entity_extraction.get("genres"):
            resolved["genres"] = _resolve_genres(entity_extraction["genres"], session)

        if entity_extraction.get("companies"):
            resolved["companies"] = _resolve_companies(entity_extraction["companies"], session)

    # Pass through numeric/date filters unchanged
    for key in ("year_after", "year_before", "rating_above", "rating_below"):
        if key in entity_extraction:
            resolved[key] = entity_extraction[key]

    logger.info("Resolved entities: %s", resolved)
    return resolved


# ---------------------------------------------------------------------------
# 4. Vector path
# ---------------------------------------------------------------------------


def query_embedding(
    user_query: str,
    openai_api_key: str,
    query_intent: str,
) -> list[float]:
    """Embed the user query. Returns empty list for CYPHER/AGGREGATE."""
    if query_intent not in ("VECTOR", "HYBRID"):
        logger.info("Skipping embedding for intent: %s", query_intent)
        return []

    client = openai.OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=user_query,
    )
    embedding = response.data[0].embedding
    logger.info("Computed query embedding (%d dims)", len(embedding))
    return embedding


def vector_results(
    query_embedding: list[float],
    neo4j_driver: Driver,
    query_intent: str,
) -> list[dict]:
    """Run vector similarity search. Returns empty list for CYPHER/AGGREGATE."""
    if query_intent not in ("VECTOR", "HYBRID") or not query_embedding:
        return []

    cypher = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $query_vector)
    YIELD node, score
    RETURN
        node.id           AS id,
        node.title        AS title,
        node.overview     AS overview,
        node.release_date AS release_date,
        node.vote_average AS vote_average,
        score
    ORDER BY score DESC
    """
    with neo4j_driver.session() as session:
        rows = session.run(
            cypher,
            {
                "index_name": VECTOR_INDEX_NAME,
                "top_k": TOP_K,
                "query_vector": query_embedding,
            },
        ).data()

    logger.info(
        "Vector search: %d results (top score: %.4f)",
        len(rows),
        rows[0]["score"] if rows else 0.0,
    )
    return rows


# ---------------------------------------------------------------------------
# 5. Cypher generation using resolved entities
# ---------------------------------------------------------------------------


def _build_entity_context(resolved: dict) -> str:
    """
    Build a plain-English summary of resolved entities for the Cypher
    generation prompt so the LLM uses exact canonical names.
    """
    if not resolved:
        return ""

    lines = ["Resolved entities to use in the query (use these EXACT values):"]

    persons = resolved.get("persons", {})
    if persons:
        for _original, canonical in persons.items():
            lines.append(f'  Person: "{canonical}"')

    movies = resolved.get("movies", {})
    if movies:
        for _original, canonical in movies.items():
            lines.append(f'  Movie title: "{canonical}"')

    genres = resolved.get("genres", {})
    if genres:
        for _original, canonical in genres.items():
            lines.append(f'  Genre: "{canonical}"')

    companies = resolved.get("companies", {})
    if companies:
        for _original, canonical in companies.items():
            lines.append(f'  ProductionCompany: "{canonical}"')

    if "year_after" in resolved:
        lines.append(f"  Date filter: m.release_date > '{resolved['year_after']}-01-01'")
    if "year_before" in resolved:
        lines.append(f"  Date filter: m.release_date < '{resolved['year_before']}-12-31'")
    if "rating_above" in resolved:
        lines.append(f"  Rating filter: m.vote_average > {resolved['rating_above']}")
    if "rating_below" in resolved:
        lines.append(f"  Rating filter: m.vote_average < {resolved['rating_below']}")

    return "\n".join(lines)


def _generate_cypher(
    user_query: str,
    entity_context: str,
    client: openai.OpenAI,
    hint: str = "",
) -> str:
    """Generate Cypher using the schema, examples, and resolved entity context."""
    system = f"""You are an expert Neo4j Cypher query generator.

Graph schema:
{SCHEMA_PROMPT}

Example queries:
{CYPHER_EXAMPLES}

{entity_context}

Rules:
- Use ONLY the exact entity names provided above — do not paraphrase or guess
- Relationship directions: (Person)-[:DIRECTED]->(Movie), (Person)-[:ACTED_IN]->(Movie),
  (Movie)-[:IN_GENRE]->(Genre), (Movie)-[:PRODUCED_BY]->(ProductionCompany)
- Use exact match {{name: 'resolved name'}} when entity is resolved, CONTAINS only as fallback
- Always alias RETURN fields with meaningful names: actor, director, movie, genre, company
- For date comparisons use STRING comparison: m.release_date > '2010-12-31'
  (release_date is stored as a string, NOT a Neo4j date type)
- For aggregation ranking queries add: WITH ..., count(m) AS film_count WHERE film_count >= 3
- For "highest rated" queries ALWAYS add WHERE m.popularity > 5 to exclude obscure low-vote films
- LIMIT 20 unless counting
- Return ONLY the Cypher query, no explanation, no markdown fences
{hint}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Generate a Cypher query for: {user_query}"},
        ],
        temperature=0.0,
        max_tokens=500,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    return raw.strip()


def _execute_cypher(cypher: str, driver: Driver) -> list[dict]:
    """Execute Cypher and return results as list of dicts."""
    try:
        with driver.session() as session:
            return session.run(cypher).data()
    except Exception as e:
        logger.warning("Cypher execution failed: %s", e)
        return []


def cypher_query(
    user_query: str,
    entity_resolution: dict,
    openai_api_key: str,
    query_intent: str,
    neo4j_driver: Driver,
) -> str:
    """
    Generate and validate a Cypher query using resolved entities.
    Retries once with a relaxed hint if first attempt returns no results.
    Returns the successful Cypher string or empty string.
    """
    if query_intent == "VECTOR":
        return ""

    client = openai.OpenAI(api_key=openai_api_key)
    entity_context = _build_entity_context(entity_resolution)

    for attempt in range(MAX_RETRIES):
        hint = ""
        if attempt == 1:
            hint = (
                "\nHINT: The previous query returned no results. "
                "Double-check relationship directions. "
                "Try broadening filters or using CONTAINS as a fallback for name matching."
            )

        cypher = _generate_cypher(user_query, entity_context, client, hint)
        logger.info("Generated Cypher (attempt %d):\n%s", attempt + 1, cypher)

        results = _execute_cypher(cypher, neo4j_driver)
        if results:
            logger.info("Cypher returned %d results", len(results))
            return cypher

        logger.warning("Cypher attempt %d returned no results", attempt + 1)

    logger.error("All Cypher attempts failed for: %s", user_query)
    return ""


def cypher_results(
    cypher_query: str,
    neo4j_driver: Driver,
) -> list[dict]:
    """Execute the validated Cypher query and return results."""
    if not cypher_query:
        return []
    results = _execute_cypher(cypher_query, neo4j_driver)
    logger.info("Cypher results: %d rows", len(results))
    return results


# ---------------------------------------------------------------------------
# 6. Enrich vector results with graph traversal
# ---------------------------------------------------------------------------


def _enrich_movie(movie_id: int, driver: Driver) -> dict | None:
    """Pull directors, cast, genres, companies for a movie node."""
    cypher = """
    MATCH (m:Movie {id: $movie_id})
    OPTIONAL MATCH (d:Person)-[:DIRECTED]->(m)
    OPTIONAL MATCH (a:Person)-[r:ACTED_IN]->(m)
    WITH m, d, a, r ORDER BY r.order ASC
    OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
    OPTIONAL MATCH (m)-[:PRODUCED_BY]->(c:ProductionCompany)
    RETURN
        m.title                                 AS title,
        m.overview                              AS overview,
        m.release_date                          AS release_date,
        m.vote_average                          AS vote_average,
        collect(DISTINCT d.name)                AS directors,
        collect(DISTINCT a.name)[0..$max_cast]  AS cast,
        collect(DISTINCT g.name)                AS genres,
        collect(DISTINCT c.name)                AS companies
    """
    with driver.session() as session:
        row = session.run(cypher, {"movie_id": movie_id, "max_cast": MAX_CAST}).single()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# 7. Merge results
# ---------------------------------------------------------------------------


def merged_results(
    vector_results: list[dict],
    cypher_results: list[dict],
    neo4j_driver: Driver,
    query_intent: str,
) -> list[dict]:
    """Merge Cypher and vector results. Cypher results come first."""
    final = []

    if cypher_results:
        final.extend({"_source": "cypher", **row} for row in cypher_results)

    if vector_results:
        seen_ids = set()
        for hit in vector_results:
            movie_id = hit.get("id")
            if movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
            enriched = _enrich_movie(movie_id, neo4j_driver)
            if enriched:
                enriched["_source"] = "vector"
                enriched["_score"] = hit.get("score", 0.0)
                final.append(enriched)

    logger.info(
        "Merged %d results (%d cypher, %d vector)",
        len(final),
        len(cypher_results),
        len([r for r in final if r.get("_source") == "vector"]),
    )
    return final


# ---------------------------------------------------------------------------
# 8. Format context
# ---------------------------------------------------------------------------


def retrieved_context(merged_results: list[dict], query_intent: str) -> str:
    """
    Format merged results into plain-text context for the generation DAG.

    Enriched movie records (from vector path) are formatted with full
    metadata. Raw Cypher rows are formatted as numbered plain-English
    lines with field labels so the LLM can read them directly.
    """
    if not merged_results:
        return "No relevant information found in the knowledge graph for this query."

    FIELD_LABELS = {
        "movie": "Movie",
        "director": "Director",
        "actor": "Actor",
        "genre": "Genre",
        "company": "Production company",
        "film_count": "Films",
        "movie_count": "Count",
        "action_movie_count": "Action movies",
        "avg_rating": "Avg rating",
        "average_rating": "Avg rating",
        "vote_average": "Rating",
        "release_date": "Released",
    }

    lines = []
    i = 0

    for row in merged_results:
        i += 1
        _source = row.get("_source", "unknown")

        if "directors" in row:
            # Enriched movie record from vector path
            directors = ", ".join(row.get("directors") or []) or "Unknown"
            cast = ", ".join(row.get("cast") or []) or "Unknown"
            genres = ", ".join(row.get("genres") or []) or "Unknown"
            companies = ", ".join(row.get("companies") or []) or "Unknown"
            release = (row.get("release_date") or "")[:4] or "N/A"
            rating = row.get("vote_average", "N/A")
            title = row.get("title", "Unknown")
            overview = row.get("overview", "")
            lines.append(f"{i}. {title} ({release}) — Rating: {rating}")
            lines.append(f"   Directed by: {directors}")
            lines.append(f"   Cast: {cast}")
            lines.append(f"   Genres: {genres}")
            lines.append(f"   Produced by: {companies}")
            if overview:
                lines.append(f"   Overview: {overview}")
            lines.append("")
        else:
            # Raw Cypher result row
            clean = {k: v for k, v in row.items() if not k.startswith("_")}
            parts = []
            for k, v in clean.items():
                label = FIELD_LABELS.get(k, k.replace("_", " ").capitalize())
                if isinstance(v, float):
                    v = round(v, 3)
                parts.append(f"{label}: {v}")
            lines.append(f"{i}. " + " | ".join(parts))

    context = "\n".join(lines)
    logger.info("Formatted context: %d chars from %d results", len(context), len(merged_results))
    return context
