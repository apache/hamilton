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


import json

import pandas as pd

movies = pd.read_csv("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_movies.csv")
credits = pd.read_csv("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_credits.csv")

with open("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_movies.json", "w") as f:
    json.dump(movies.to_dict(orient="records"), f)

with open("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_credits.json", "w") as f:
    json.dump(credits.to_dict(orient="records"), f)
