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
Static schema definitions for the TMDB movie knowledge graph.

Nodes
-----
Movie           : id, title, release_date, overview, popularity, vote_average
Person          : id, name
Genre           : name
ProductionCompany : id, name

Relationships
-------------
(:Person)-[:ACTED_IN {order: int, character: str}]->(:Movie)
(:Person)-[:DIRECTED]->(:Movie)
(:Movie)-[:IN_GENRE]->(:Genre)
(:Movie)-[:PRODUCED_BY]->(:ProductionCompany)

Constraints (applied at ingestion time via run.py)
-----------
UNIQUE Movie.id
UNIQUE Person.id
UNIQUE Genre.name
UNIQUE ProductionCompany.id
"""

# Node labels
NODE_MOVIE = "Movie"
NODE_PERSON = "Person"
NODE_GENRE = "Genre"
NODE_COMPANY = "ProductionCompany"

# Relationship types
REL_ACTED_IN = "ACTED_IN"
REL_DIRECTED = "DIRECTED"
REL_IN_GENRE = "IN_GENRE"
REL_PRODUCED_BY = "PRODUCED_BY"

# Properties stored per node type
NODE_PROPERTIES = {
    NODE_MOVIE: ["id", "title", "release_date", "overview", "popularity", "vote_average"],
    NODE_PERSON: ["id", "name"],
    NODE_GENRE: ["name"],
    NODE_COMPANY: ["id", "name"],
}

# Properties stored per relationship type
REL_PROPERTIES = {
    REL_ACTED_IN: ["order", "character"],
    REL_DIRECTED: [],
    REL_IN_GENRE: [],
    REL_PRODUCED_BY: [],
}

# Connectivity map  src -> rel -> dest
CONNECTIVITY = [
    (NODE_PERSON, REL_ACTED_IN, NODE_MOVIE),
    (NODE_PERSON, REL_DIRECTED, NODE_MOVIE),
    (NODE_MOVIE, REL_IN_GENRE, NODE_GENRE),
    (NODE_MOVIE, REL_PRODUCED_BY, NODE_COMPANY),
]

# Cypher constraints to create before ingestion
CONSTRAINTS = [
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NODE_MOVIE}) REQUIRE n.id IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NODE_PERSON}) REQUIRE n.id IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NODE_GENRE}) REQUIRE n.name IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NODE_COMPANY}) REQUIRE n.id IS UNIQUE",
]


def schema_to_prompt() -> str:
    """
    Returns a natural-language description of the graph schema
    for use in LLM system prompts.
    """
    lines = ["The knowledge graph contains the following node types:\n"]

    for label, props in NODE_PROPERTIES.items():
        if props:
            lines.append(f"  {label}: {', '.join(props)}")
        else:
            lines.append(f"  {label}: (no properties)")

    lines.append("\nThe knowledge graph contains the following relationship types:\n")

    for src, rel, dest in CONNECTIVITY:
        props = REL_PROPERTIES.get(rel, [])
        prop_str = f" with properties: {', '.join(props)}" if props else ""
        lines.append(f"  (:{src})-[:{rel}]->(:{dest}){prop_str}")

    return "\n".join(lines)