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
Code courtesy of the FalkorDB.
"""


# collect graph's schema
def graph_schema(g):
    schema = {}

    # ---------------------------------------------------------------------------
    # process nodes
    # ---------------------------------------------------------------------------

    nodes = {}

    q = "CALL db.labels()"
    labels = [x[0] for x in g.query(q).result_set]

    for label in labels:
        nodes[label] = {}
        nodes[label]["attributes"] = {}

        q = f"MATCH (n:{label}) RETURN n LIMIT 50"
        result = g.query(q).result_set

        for row in result:
            node = row[0]
            for attr in node.properties:
                val = node.properties[attr]
                if attr not in nodes[label]["attributes"]:
                    nodes[label]["attributes"][attr] = {"type": type(val).__name__}

    schema["nodes"] = nodes

    # ---------------------------------------------------------------------------
    # process relations
    # ---------------------------------------------------------------------------

    edges = {}

    q = "CALL db.relationshiptypes()"
    rels = [x[0] for x in g.query(q).result_set]

    for r in rels:
        edges[r] = {}
        edges[r]["attributes"] = {}

        q = f"MATCH ()-[e:{r}]->() RETURN e LIMIT 50"
        result = g.query(q).result_set

        for row in result:
            edge = row[0]
            for attr in edge.properties:
                val = edge.properties[attr]
                if attr not in edges[r]["attributes"]:
                    edges[r]["attributes"][attr] = {"type": type(val).__name__}

        edges[r]["connects"] = []

        # collect edge endpoints
        for src in labels:
            for dest in labels:
                q = f"MATCH (:{src})-[:{r}]->(:{dest}) RETURN 1 LIMIT 1"
                res = g.query(q).result_set
                if len(res) == 1:
                    edges[r]["connects"].append((src, dest))

    schema["edges"] = edges

    return schema
